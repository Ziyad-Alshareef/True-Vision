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
    # Check if we're running on Heroku
    on_heroku = os.environ.get('DYNO') is not None
    
    if on_heroku:
        # Heroku-specific paths - try these first when on Heroku
        possible_paths = [
            # Heroku buildpack location - most reliable for Heroku
            '/app/vendor/ffmpeg/bin/ffmpeg',
            # Standard Heroku paths
            '/app/vendor/ffmpeg/ffmpeg',
            '/usr/bin/ffmpeg',
            # Fallback to system PATH
            'ffmpeg',
        ]
    else:
        # Local development paths
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin', 'ffmpeg-6.1.1-essentials_build', 'bin', 'ffmpeg.exe'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin', 'ffmpeg-6.1.1-essentials_build', 'bin', 'ffmpeg'),
            # Fallback to system PATH
            'ffmpeg',
        ]
    
    # Check if any of the paths exist
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found ffmpeg at: {path}")
            # Check if the file is executable
            if on_heroku and not os.access(path, os.X_OK):
                print(f"Warning: FFmpeg found at {path} but it's not executable")
                try:
                    os.chmod(path, 0o755)  # Try to make it executable
                    print(f"Made FFmpeg at {path} executable")
                except Exception as e:
                    print(f"Failed to make FFmpeg executable: {e}")
            return path
    
    # Fallback to system PATH
    print("Using ffmpeg from system PATH")
    return 'ffmpeg'

def get_ffprobe_path():
    """Get the path to the ffprobe executable based on the project structure."""
    # Check if we're running on Heroku
    on_heroku = os.environ.get('DYNO') is not None
    
    if on_heroku:
        # Heroku-specific paths - try these first when on Heroku
        possible_paths = [
            # Heroku buildpack location - most reliable for Heroku
            '/app/vendor/ffmpeg/bin/ffprobe',
            # Standard Heroku paths
            '/app/vendor/ffmpeg/ffprobe',
            '/usr/bin/ffprobe',
            # Fallback to system PATH
            'ffprobe',
        ]
    else:
        # Local development paths
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin', 'ffmpeg-6.1.1-essentials_build', 'bin', 'ffprobe.exe'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin', 'ffmpeg-6.1.1-essentials_build', 'bin', 'ffprobe'),
            # Fallback to system PATH
            'ffprobe',
        ]
    
    # Check if any of the paths exist
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found ffprobe at: {path}")
            # Check if the file is executable
            if on_heroku and not os.access(path, os.X_OK):
                print(f"Warning: FFprobe found at {path} but it's not executable")
                try:
                    os.chmod(path, 0o755)  # Try to make it executable
                    print(f"Made FFprobe at {path} executable")
                except Exception as e:
                    print(f"Failed to make FFprobe executable: {e}")
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
            
            # Make sure the file doesn't already exist (could cause issues with ffmpeg -y flag)
            try:
                if os.path.exists(temp_thumb_path):
                    os.unlink(temp_thumb_path)
                    print(f"Removed existing temporary thumbnail file")
            except Exception as e:
                print(f"Error removing existing thumbnail file: {str(e)}")
            
            # Save the video to a temporary file if using S3
            if hasattr(self.Video_File, 'url'):
                with tempfile.NamedTemporaryFile(suffix=os.path.splitext(self.Video_File.name)[1], delete=False) as temp_video:
                    temp_video_path = temp_video.name
                    print(f"Created temporary video file: {temp_video_path}")
                    # Download the file from S3
                    try:
                        video_data = self.Video_File.read()
                        print(f"Read {len(video_data)} bytes from S3")
                        
                        # Check the first few bytes to determine if it's really a video file
                        if len(video_data) > 16:
                            magic_bytes = video_data[:16].hex()
                            print(f"File magic bytes: {magic_bytes}")
                            
                            # Check for common video signatures
                            is_mp4 = magic_bytes.startswith('00000020667479706d703432') or magic_bytes.startswith('000000186674797033677035') or magic_bytes.startswith('0000001c667479704d534e56')
                            is_avi = magic_bytes.startswith('52494646') and 'AVI' in video_data[:32].decode('utf-8', errors='ignore')
                            is_mov = magic_bytes.startswith('0000001466747970') or magic_bytes.startswith('6d6f6f76')
                            is_webm = magic_bytes.startswith('1a45dfa3')
                            
                            if is_mp4:
                                print("Detected MP4 video format")
                            elif is_avi:
                                print("Detected AVI video format")
                            elif is_mov:
                                print("Detected MOV/QuickTime video format")
                            elif is_webm:
                                print("Detected WebM video format")
                            else:
                                print("Unknown or non-video file format. This might not be a valid video file.")
                        
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
                        '-y',  # Force overwrite if file exists
                        temp_thumb_path
                    ]
                    print(f"Running FFmpeg command: {' '.join(cmd)}")
                    
                    # Use subprocess without check=True to capture error output
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    # Print ffmpeg output regardless of success/failure
                    print(f"FFmpeg stdout: {result.stdout}")
                    print(f"FFmpeg stderr: {result.stderr}")
                    print(f"FFmpeg exit code: {result.returncode}")
                    
                    # Check temp file directory permissions
                    temp_dir = os.path.dirname(temp_thumb_path)
                    print(f"Temp directory permissions for {temp_dir}: {oct(os.stat(temp_dir).st_mode)[-3:]}")
                    print(f"Temp directory writeable: {os.access(temp_dir, os.W_OK)}")
                    
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
                    # Run without check=True to capture errors
                    duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
                    
                    # Print ffprobe output regardless of success/failure
                    print(f"FFprobe stdout: {duration_result.stdout}")
                    print(f"FFprobe stderr: {duration_result.stderr}")
                    print(f"FFprobe exit code: {duration_result.returncode}")
                    
                    # Only proceed if successful
                    if duration_result.returncode == 0 and duration_result.stdout.strip():
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
                            '-y',  # Force overwrite if file exists
                            temp_thumb_path
                        ]
                        # Run without check=True
                        seek_result = subprocess.run(seek_cmd, capture_output=True, text=True)
                        
                        # Print output
                        print(f"FFmpeg seek stdout: {seek_result.stdout}")
                        print(f"FFmpeg seek stderr: {seek_result.stderr}")
                        print(f"FFmpeg seek exit code: {seek_result.returncode}")
                        
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
                    else:
                        print(f"Failed to get duration: {duration_result.stderr}")
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
                        '-y',  # Force overwrite if file exists
                        temp_thumb_path
                    ]
                    try:
                        # Run without check=True
                        thumb_result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        # Print output
                        print(f"FFmpeg thumbnail filter stdout: {thumb_result.stdout}")
                        print(f"FFmpeg thumbnail filter stderr: {thumb_result.stderr}")
                        print(f"FFmpeg thumbnail filter exit code: {thumb_result.returncode}")
                        
                        print("Thumbnail filter completed")
                        success = os.path.exists(temp_thumb_path) and os.path.getsize(temp_thumb_path) > 100
                        print(f"Thumbnail filter result: {success}, {os.path.getsize(temp_thumb_path) if os.path.exists(temp_thumb_path) else 0} bytes")
                    except Exception as e:
                        print(f"Error using thumbnail filter: {str(e)}")
                        
                # If still not successful, try with direct file sizes
                if not success:
                    print("Trying with direct file output approach")
                    output_jpg = f"/tmp/direct_output_{self.Video_id}.jpg"
                    cmd = [
                        get_ffmpeg_path(),
                        '-i', temp_video_path,
                        '-f', 'mjpeg',  # Force MJPEG output
                        '-frames:v', '1',
                        '-y',  # Force overwrite if file exists
                        output_jpg
                    ]
                    try:
                        direct_result = subprocess.run(cmd, capture_output=True, text=True)
                        print(f"Direct FFmpeg command exit code: {direct_result.returncode}")
                        print(f"Direct FFmpeg stderr: {direct_result.stderr}")
                        
                        if os.path.exists(output_jpg) and os.path.getsize(output_jpg) > 100:
                            print(f"Successfully created direct output at {output_jpg} with size {os.path.getsize(output_jpg)}")
                            
                            # Copy the direct output to our temp thumb path
                            import shutil
                            shutil.copy2(output_jpg, temp_thumb_path)
                            
                            # Check if it's valid
                            img = Image.open(temp_thumb_path)
                            extrema = img.convert("L").getextrema()
                            if extrema[1] - extrema[0] > 30:
                                success = True
                                print("Direct output approach succeeded")
                            else:
                                print("Direct output is too dark/uniform")
                        else:
                            print(f"Direct output failed, file exists: {os.path.exists(output_jpg)}, size: {os.path.getsize(output_jpg) if os.path.exists(output_jpg) else 0}")
                    except Exception as e:
                        print(f"Error with direct output approach: {str(e)}")
            
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
        except Exception as e:
            print(f"Error in thumbnail generation process: {e}")
            # If all else fails, create a colored placeholder
            try:
                # Create a colored placeholder image
                print("Creating colored placeholder image")
                
                # Make absolutely sure this doesn't fail
                try:
                    img = Image.new('RGB', (480, 320), color=(32, 127, 77))  # Green color
                    draw = ImageDraw.Draw(img)
                    
                    # Try to add text, but don't fail if it doesn't work
                    try:
                        draw.text((240, 160), "True Vision", fill=(255, 255, 255), anchor="mm")
                    except Exception as text_error:
                        print(f"Could not add text to placeholder: {text_error}")
                        # Continue without text
                    
                    # Save to buffer
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG')
                    buffer.seek(0)
                    
                    # Save placeholder as thumbnail
                    file_name = f"placeholder_{self.Video_id}.jpg"
                    self.Thumbnail.save(file_name, ContentFile(buffer.read()), save=False)
                    print(f"Created placeholder thumbnail: {file_name}")
                    return False
                except Exception as img_error:
                    print(f"Error creating image: {img_error}")
                    
                    # Even more basic fallback - create a 1x1 pixel image if PIL fails
                    try:
                        print("Attempting ultra-basic 1x1 pixel fallback")
                        # Create a 1x1 green pixel as JPG
                        one_pixel = bytes([
                            0xFF, 0xD8,  # JPEG SOI marker
                            0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00,  # JFIF header
                            0xFF, 0xDB, 0x00, 0x43, 0x00, 0x10, 0x0B, 0x0C, 0x0E, 0x0C, 0x0A, 0x10, 0x0E, 0x0D, 0x0E, 0x12, 0x11, 0x10, 0x13, 0x18, 0x28, 0x1A, 0x18, 0x16, 0x16, 0x18, 0x31, 0x23, 0x25, 0x1D, 0x28, 0x3A, 0x33, 0x3D, 0x3C, 0x39, 0x33, 0x38, 0x37, 0x40, 0x48, 0x5C, 0x4E, 0x40, 0x44, 0x57, 0x45, 0x37, 0x38, 0x50, 0x6D, 0x51, 0x57, 0x5F, 0x62, 0x67, 0x68, 0x67, 0x3E, 0x4D, 0x71, 0x79, 0x70, 0x64, 0x78, 0x5C, 0x65, 0x67, 0x63,  # DQT
                            0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0x11, 0x00,  # SOF
                            0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B,  # DHT
                            0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03, 0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D, 0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA,  # DHT (continued)
                            0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0x37, 0x7F, 0xFF, 0xD9  # SOS + EOI
                        ])
                        
                        buffer = io.BytesIO(one_pixel)
                        file_name = f"placeholder_{self.Video_id}.jpg"
                        self.Thumbnail.save(file_name, ContentFile(buffer.read()), save=False)
                        print(f"Created 1x1 pixel fallback thumbnail: {file_name}")
                        return False
                    except Exception as pixel_error:
                        print(f"Even 1x1 pixel creation failed: {pixel_error}")
                        
                        # Absolute last resort - use a pre-defined base64 encoded green pixel
                        try:
                            print("Attempting base64 encoded fallback")
                            import base64
                            # This is a base64 encoded 1x1 green pixel JPG
                            base64_jpg = '/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDAREAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACv/EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AN/8A/9k='
                            binary_data = base64.b64decode(base64_jpg)
                            buffer = io.BytesIO(binary_data)
                            file_name = f"placeholder_{self.Video_id}.jpg"
                            self.Thumbnail.save(file_name, ContentFile(buffer.read()), save=False)
                            print(f"Created base64 fallback thumbnail: {file_name}")
                            return False
                        except Exception as base64_error:
                            print(f"Even base64 fallback failed: {base64_error}")
                            # At this point, there's nothing more we can do
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
