from django.contrib.auth.models import AbstractUser
from django.db import models
import json
from django.utils import timezone
import random
import datetime
from storages.backends.s3boto3 import S3Boto3Storage
import os
import subprocess
import tempfile
from django.core.files.base import ContentFile
from PIL import Image
import io
from PIL import ImageEnhance
from PIL import ImageDraw

# Add this function to get the ffmpeg executable path
def get_ffmpeg_path():
    """Get the path to the ffmpeg executable based on the project structure."""
    # Check multiple possible locations for ffmpeg
    possible_paths = [
        # Local development paths
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin', 'ffmpeg-6.1.1-essentials_build', 'bin', 'ffmpeg.exe'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin', 'ffmpeg-6.1.1-essentials_build', 'bin', 'ffmpeg'),
        # Standard Heroku paths
        '/app/vendor/ffmpeg/ffmpeg',
        '/usr/bin/ffmpeg',
        # Heroku buildpack location - most reliable for Heroku
        '/app/vendor/ffmpeg/bin/ffmpeg',
    ]
    
    # Check if any of the paths exist
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found ffmpeg at: {path}")
            return path
    
    # Fallback to system PATH
    print("Using ffmpeg from system PATH")
    return 'ffmpeg'

def get_ffprobe_path():
    """Get the path to the ffprobe executable based on the project structure."""
    # Check multiple possible locations for ffprobe
    possible_paths = [
        # Local development paths
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin', 'ffmpeg-6.1.1-essentials_build', 'bin', 'ffprobe.exe'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin', 'ffmpeg-6.1.1-essentials_build', 'bin', 'ffprobe'),
        # Standard Heroku paths
        '/app/vendor/ffmpeg/ffprobe',
        '/usr/bin/ffprobe',
        # Heroku buildpack location - most reliable for Heroku
        '/app/vendor/ffmpeg/bin/ffprobe',
    ]
    
    # Check if any of the paths exist
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found ffprobe at: {path}")
            return path
    
    # Fallback to system PATH
    print("Using ffprobe from system PATH")
    return 'ffprobe'

class S3MediaStorage(S3Boto3Storage):
    """Custom S3 storage for media files"""
    location = 'media'
    file_overwrite = False
    default_acl = None  # Disable ACL

class S3FrameStorage(S3Boto3Storage):
    """Custom S3 storage for video frames"""
    location = 'frames'
    file_overwrite = False
    default_acl = None  # Disable ACL

class CustomUser(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    reset_password_pin = models.CharField(max_length=6, blank=True, null=True)
    reset_password_pin_expiration = models.DateTimeField(blank=True, null=True)
    
    def generate_reset_pin(self):
        """Generate a 6-digit PIN for password reset"""
        self.reset_password_pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.reset_password_pin_expiration = timezone.now() + datetime.timedelta(minutes=10)  # 10 minutes expiration
        self.save()
        return self.reset_password_pin
    
    def is_reset_pin_valid(self, input_pin):
        """Check if the reset PIN is valid and not expired"""
        if not self.reset_password_pin or not self.reset_password_pin_expiration:
            return False
        if self.reset_password_pin != input_pin:
            return False
        if timezone.now() > self.reset_password_pin_expiration:
            return False
        return True
    
    def clear_reset_pin(self):
        """Clear the reset PIN after it's used"""
        self.reset_password_pin = None
        self.reset_password_pin_expiration = None
        self.save()

class Model(models.Model):
    """ML model metadata"""
    Model_id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=255)
    Version = models.CharField(max_length=255)
    Description = models.TextField()

class Video(models.Model):
    """Video file and metadata"""
    Video_id = models.AutoField(primary_key=True)
    User_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    Video_File = models.FileField(storage=S3MediaStorage(), upload_to='videos/', null=True)
    Video_Path = models.TextField(help_text="S3 path to the video file")
    Thumbnail = models.ImageField(storage=S3MediaStorage(), upload_to='thumbnails/', null=True, blank=True, help_text="Representative frame of the video")
    isAnalyzed = models.BooleanField(default=False)
    size = models.BigIntegerField()
    Length = models.IntegerField()
    Resolution = models.CharField(max_length=255)
    Uploaded_at = models.DateTimeField(auto_now_add=True)
    Frame_per_Second = models.BigIntegerField()
    
    def save(self, *args, **kwargs):
        """Override save to update Video_Path from Video_File and generate thumbnail"""
        is_new = self.pk is None
        
        # First save to get the file path
        super().save(*args, **kwargs)
        
        # Update Video_Path if not set
        if self.Video_File and not self.Video_Path:
            self.Video_Path = self.Video_File.url
            super().save(update_fields=['Video_Path'])
        
        # Generate thumbnail if this is a new video and we don't have a thumbnail yet
        if is_new and self.Video_File and not self.Thumbnail:
            self.generate_thumbnail()
            super().save(update_fields=['Thumbnail'])
    
    def generate_thumbnail(self):
        """Generate a thumbnail from the video"""
        print(f"Starting thumbnail generation for video ID {self.Video_id}")
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_thumb:
                temp_thumb_path = temp_thumb.name
            print(f"Created temporary thumbnail file: {temp_thumb_path}")
            
            # Save the video to a temporary file if using S3
            if hasattr(self.Video_File, 'url'):
                with tempfile.NamedTemporaryFile(suffix=os.path.splitext(self.Video_File.name)[1], delete=False) as temp_video:
                    temp_video_path = temp_video.name
                    print(f"Created temporary video file: {temp_video_path}")
                    # Download the file from S3
                    try:
                        video_data = self.Video_File.read()
                        print(f"Read {len(video_data)} bytes from S3")
                        temp_video.write(video_data)
                        print(f"Successfully wrote video data to temp file")
                    except Exception as e:
                        print(f"Error reading from S3: {str(e)}")
                        raise
            else:
                # The file is local
                temp_video_path = self.Video_File.path
                print(f"Using local video path: {temp_video_path}")
            
            # Use ffmpeg to extract a frame from the middle of the video
            # Try different timestamps to avoid black frames
            timestamps = ['00:00:01', '00:00:03', '00:00:05', '00:00:10', '00:00:15', '00:00:20', '00:00:30']
            success = False
            
            for timestamp in timestamps:
                try:
                    print(f"Attempting thumbnail extraction at timestamp {timestamp}")
                    # Try this timestamp
                    cmd = [
                        get_ffmpeg_path(),
                        '-i', temp_video_path,
                        '-ss', timestamp,  # timestamp into the video
                        '-vframes', '1',
                        '-q:v', '2',  # Higher quality setting
                        '-f', 'image2',
                        temp_thumb_path
                    ]
                    print(f"Running FFmpeg command: {' '.join(cmd)}")
                    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                    
                    # Check if the file was created and has content
                    if os.path.exists(temp_thumb_path) and os.path.getsize(temp_thumb_path) > 100:
                        print(f"Thumbnail file created successfully: {os.path.getsize(temp_thumb_path)} bytes")
                        
                        # Check if the image is not just black
                        img = Image.open(temp_thumb_path)
                        extrema = img.convert("L").getextrema()
                        print(f"Image extrema (min/max): {extrema}")
                        
                        # If min and max are too similar, the image is likely just one color (black)
                        if extrema[1] - extrema[0] > 30:
                            success = True
                            print(f"Generated valid thumbnail at timestamp {timestamp}")
                            break
                        else:
                            print(f"Thumbnail at {timestamp} is too dark/uniform, trying next timestamp...")
                    else:
                        print(f"Thumbnail file is missing or too small: {os.path.exists(temp_thumb_path)}, {os.path.getsize(temp_thumb_path) if os.path.exists(temp_thumb_path) else 0}")
                except subprocess.CalledProcessError as e:
                    print(f"Error generating thumbnail at {timestamp}: {e}")
                    print(f"FFMPEG stderr: {e.stderr}")
                    print(f"FFMPEG stdout: {e.stdout}")
                    continue
                except Exception as e:
                    print(f"Unexpected error during thumbnail generation at {timestamp}: {str(e)}")
                    continue
            
            if not success:
                print("All thumbnail attempts with timestamps failed, trying alternative approaches")
                
                # Try a different approach - seek to 10% of video duration
                try:
                    print("Trying to determine video duration...")
                    # Get video duration
                    duration_cmd = [
                        get_ffprobe_path(),
                        '-v', 'error',
                        '-show_entries', 'format=duration',
                        '-of', 'default=noprint_wrappers=1:nokey=1',
                        temp_video_path
                    ]
                    duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
                    duration = float(duration_result.stdout.strip())
                    print(f"Video duration: {duration} seconds")
                    
                    # Try 10% into the video
                    ten_percent = max(1, int(duration * 0.1))
                    seek_timestamp = f"00:00:{ten_percent}"
                    print(f"Trying to extract thumbnail at {seek_timestamp} (10% of duration)")
                    
                    seek_cmd = [
                        get_ffmpeg_path(),
                        '-i', temp_video_path,
                        '-ss', seek_timestamp,
                        '-vframes', '1',
                        '-q:v', '2',
                        '-f', 'image2',
                        temp_thumb_path
                    ]
                    subprocess.run(seek_cmd, capture_output=True, check=True)
                    
                    # Check if the image is valid
                    if os.path.exists(temp_thumb_path) and os.path.getsize(temp_thumb_path) > 100:
                        img = Image.open(temp_thumb_path)
                        extrema = img.convert("L").getextrema()
                        if extrema[1] - extrema[0] > 30:
                            success = True
                            print(f"Generated valid thumbnail at 10% of duration")
                        else:
                            print("Thumbnail at 10% is too dark/uniform")
                    else:
                        print("Failed to create thumbnail at 10% of duration")
                except Exception as e:
                    print(f"Error with duration-based approach: {str(e)}")
                
                # If still not successful, try the thumbnail filter
                if not success:
                    print("Using thumbnail filter as fallback")
                    # Fallback to a simpler approach
                    cmd = [
                        get_ffmpeg_path(),
                        '-i', temp_video_path,
                        '-vf', 'thumbnail,scale=480:320',  # Use thumbnail filter
                        '-frames:v', '1',
                        temp_thumb_path
                    ]
                    try:
                        subprocess.run(cmd, check=True, capture_output=True)
                        print("Thumbnail filter completed")
                        success = os.path.exists(temp_thumb_path) and os.path.getsize(temp_thumb_path) > 100
                        print(f"Thumbnail filter result: {success}, {os.path.getsize(temp_thumb_path) if os.path.exists(temp_thumb_path) else 0} bytes")
                    except Exception as e:
                        print(f"Error using thumbnail filter: {str(e)}")
            
            # Process the thumbnail if we have one
            if success:
                print("Opening generated thumbnail")
                # Open the generated thumbnail
                with open(temp_thumb_path, 'rb') as f:
                    thumb_data = f.read()
                
                # Resize if needed
                img = Image.open(io.BytesIO(thumb_data))
                print(f"Thumbnail dimensions: {img.width}x{img.height}, mode: {img.mode}")
                # Keep aspect ratio but limit to 480px max dimension
                img.thumbnail((480, 480))
                print(f"Resized to: {img.width}x{img.height}")
                
                # Ensure image is RGB (in case it's grayscale/RGBA)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    print(f"Converted image to RGB mode")
                
                # Increase brightness and contrast slightly if the image is dark
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.2)  # Increase brightness by 20%
                
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.2)  # Increase contrast by 20%
                print("Applied brightness and contrast enhancements")
                
                # Save to in-memory buffer
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=95)
                buffer.seek(0)
                print("Saved enhanced image to buffer")
                
                # Set the thumbnail field
                file_name = f"thumbnail_{self.Video_id}.jpg"
                self.Thumbnail.save(file_name, ContentFile(buffer.read()), save=False)
                print(f"Successfully saved thumbnail as {file_name}")
                
                # Clean up temp files
                try:
                    os.unlink(temp_thumb_path)
                    if hasattr(self.Video_File, 'url'):
                        os.unlink(temp_video_path)
                    print("Cleaned up temporary files")
                except Exception as e:
                    print(f"Error cleaning up: {str(e)}")
                
                return True
            else:
                print("All thumbnail generation attempts failed, creating placeholder")
                raise Exception("Could not generate valid thumbnail")
                
        except Exception as e:
            print(f"Error in thumbnail generation process: {e}")
            # If all else fails, create a colored placeholder
            try:
                # Create a colored placeholder image
                print("Creating colored placeholder image")
                img = Image.new('RGB', (480, 320), color=(32, 127, 77))  # Green color
                draw = ImageDraw.Draw(img)
                draw.text((240, 160), "True Vision", fill=(255, 255, 255), anchor="mm")
                
                # Save to buffer
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG')
                buffer.seek(0)
                
                # Save placeholder as thumbnail
                file_name = f"placeholder_{self.Video_id}.jpg"
                self.Thumbnail.save(file_name, ContentFile(buffer.read()), save=False)
                print(f"Created placeholder thumbnail: {file_name}")
                return False
            except Exception as e2:
                print(f"Even placeholder creation failed: {e2}")
                return False

class Detection(models.Model):
    """Detection results from video analysis"""
    Result_id = models.AutoField(primary_key=True)
    Video_id = models.ForeignKey(Video, on_delete=models.CASCADE)

class DetectionModel(models.Model):
    """Links models to detection results"""
    Model_id = models.ForeignKey(Model, on_delete=models.CASCADE)
    Result_id = models.ForeignKey(Detection, on_delete=models.CASCADE)
    Confidence = models.DecimalField(max_digits=5, decimal_places=2, help_text="Confidence score (0-100)")
    Result = models.CharField(max_length=255, choices=[
        ('real', 'Real'),
        ('fake', 'Fake'),
    ])
    Detected_at = models.DateTimeField(auto_now_add=True)

class Analysis(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    video = models.FileField(storage=S3MediaStorage(), upload_to='uploads/')
    result = models.TextField()  # Changed from JSONField to TextField
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def set_result(self, value):
        self.result = json.dumps(value)
    
    def get_result(self):
        try:
            return json.loads(self.result)
        except:
            return {}
        
'''from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import transaction, OperationalError

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('operator', 'Operator'),
    )

    email = models.EmailField(max_length=255, unique=True)  # Unique email
    password = models.CharField(max_length=255)  # Password field
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Phone number for Operators
    organization = models.CharField(max_length=255, unique=True, blank=True, null=True)  # Organization for Operators
    role = models.CharField(max_length=8, choices=ROLE_CHOICES, default='operator')  # Role (admin or operator)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    authorized = models.BooleanField(default=False)  # Specific for Operators, if applicable
    pin = models.CharField(max_length=6, blank=True, null=True)
    pin_expiration = models.DateTimeField(blank=True, null=True)

    
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def generate_pin(self):
        self.pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.pin_expiration = datetime.datetime.now() + datetime.timedelta(minutes=10)  # 10 minutes expiration
        self.save()

    def pin_is_valid(self, input_pin):
        # Make sure the current time is timezone-aware
        return self.pin == input_pin and self.pin_expiration > timezone.now()

    def __str__(self):
        return self.email


class Note(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")

    def __str__(self):
        return self.title




from django.utils import timezone
import random
import threading
import time
from django.conf import settings

class ParkingSpotsMap(models.Model):
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # assuming you use Django's built-in User model
    name=models.CharField(max_length=10)
    length = models.IntegerField()
    width = models.IntegerField()
    orientation = models.CharField(max_length=10, choices=[('horizontal', 'Horizontal'), ('vertical', 'Vertical')])
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    org = models.CharField(max_length=255, blank=True, null=True)  # Organization for Operators
    email = models.EmailField(max_length=255)
    loc = models.CharField(max_length=255)

    def __str__(self):
        return f"Map {self.id} by {self.operator.email}"

class ParkingSpot(models.Model):
    parking_spots_map = models.ForeignKey(ParkingSpotsMap, on_delete=models.CASCADE)
    x_axis = models.IntegerField()
    y_axis = models.IntegerField()
    sensor_status = models.CharField(max_length=10, choices=[('used', 'Used'), ('unused', 'Unused')])
    status = models.CharField(max_length=20, choices=[
        ('sensor', 'Sensor Status'),
        ('maintenance', 'Maintenance'),
        ('unavailable', 'Unavailable'),
        ('road', 'Road')
    ], default='sensor')

    def __str__(self):
        return f"Parking Spot {self.id}"
    
    def flip_status(self):
        retries = 5  # Number of retries for saving
        while retries > 0:
            try:
                with transaction.atomic():  # Ensure atomic database transaction
                    if self.sensor_status == 'unused' and random.random() < 0.15:
                        self.sensor_status = 'used'
                    elif self.sensor_status == 'used' and random.random() < 0.10:
                        self.sensor_status = 'unused'
                    self.save()
                break  # Exit the loop if successful
            except OperationalError:  # Handle any database locking errors
                retries -= 1
                time.sleep(0.5)  # Wait for 500ms before retrying
        if retries == 0:
            print(f"Failed to update parking spot {self.id} after several retries.")


class VirtualSensor(models.Model):
    parking_spot = models.OneToOneField(ParkingSpot, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[('used', 'Used'), ('unused', 'Unused')], default='unused')

    def __str__(self):
        return f"Sensor for Spot {self.parking_spot.id}"

    def flip_status(self):
        retries = 5  # Number of retries for saving
        while retries > 0:
            try:
                with transaction.atomic():  # Ensure atomic database transaction
                    if self.sensor_status == 'unused' and random.random() < 0.90:
                        self.sensor_status = 'used'
                    elif self.sensor_status == 'used' and random.random() < 0.85:
                        self.sensor_status = 'unused'
                    self.save()
                break  # Exit the loop if successful
            except OperationalError:  # Handle any database locking errors
                retries -= 1
                time.sleep(0.5)  # Wait for 500ms before retrying
        if retries == 0:
            print(f"Failed to update parking spot {self.id} after several retries.")

def run_virtual_sensor_algorithm():
    while True:
        # Get all parking spot IDs
        all_spots = list(ParkingSpot.objects.values_list('id', flat=True))
        
        # Randomly select a subset of parking spots (e.g., 15% of all spots)
        num_spots = int(len(all_spots) * 0.15)  # Adjust percentage as needed
        selected_spots = random.sample(all_spots, num_spots) if num_spots > 0 else []
        
        # Update the randomly selected spots
        for spot_id in selected_spots:
            try:
                spot = ParkingSpot.objects.get(id=spot_id)
                spot.flip_status()
            except ParkingSpot.DoesNotExist:
                print(f"ParkingSpot with id {spot_id} does not exist.")
            except Exception as e:
                print(f"Error occurred while updating ParkingSpot {spot_id}: {e}")
        
        time.sleep(10)  # Run every 10 seconds

# Starting the background algorithm
#thread = threading.Thread(target=run_virtual_sensor_algorithm)
#thread.daemon = True
#thread.start()


import random
import datetime
''''''
class Operator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pin = models.CharField(max_length=6, blank=True, null=True)
    pin_expiration = models.DateTimeField(blank=True, null=True)

    def generate_pin(self):
        self.pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.pin_expiration = datetime.datetime.now() + datetime.timedelta(minutes=10)  # 10 minutes expiration
        self.save()

    def pin_is_valid(self, input_pin):
        return self.pin == input_pin and self.pin_expiration > datetime.datetime.now()

# Add this new model
class MapReport(models.Model):
    parking_map = models.ForeignKey(ParkingSpotsMap, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    font_size = models.CharField(max_length=10, default='16px')
    font_family = models.CharField(max_length=50, default='Arial')
    text_align = models.CharField(max_length=10, default='left')
    font_weight = models.CharField(max_length=10, default='normal')
    font_style = models.CharField(max_length=10, default='normal')

    def __str__(self):
        return f"Report for Map {self.parking_map.id}"
'''
'''
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Add custom fields here if needed
    pass

class Analysis(models.Model):
    user = models.ForeignKey('api.CustomUser', on_delete=models.CASCADE)
    video = models.FileField(upload_to='uploads/')
    result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
'''
