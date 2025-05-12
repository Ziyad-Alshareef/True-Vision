from rest_framework import status
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, authenticate
from .models import Analysis, Video, Model, Detection, DetectionModel, CustomUser, DeepFakeDetection
from .serializers import CustomUserSerializer, AnalysisSerializer, VideoSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import serializers
import boto3
from datetime import datetime
from django.conf import settings
from botocore.exceptions import ClientError
import os
import json
import tempfile
import subprocess
import requests
from django.http import HttpResponse, StreamingHttpResponse
import mimetypes
# Import the deepfake detector
from .detector import detect_deepfake
import logging
from django.core.mail import send_mail
from django.utils import timezone

# Get the user model (now points to CustomUser)
User = get_user_model()

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                self.perform_create(serializer)
                return Response(
                    {"message": "User created successfully"},
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                # Log the error
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating user: {str(e)}")
                
                # Check for duplicate email error
                if 'email' in str(e) and 'already exists' in str(e):
                    return Response(
                        {"email": ["This email is already registered"]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Check for duplicate username error
                elif 'username' in str(e) and 'already exists' in str(e):
                    return Response(
                        {"username": ["This username is already taken"]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Generic error
                return Response(
                    {"error": "Registration failed. Please try again."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AnalysisViewSet(viewsets.ModelViewSet):
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return Analysis.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        video = request.FILES.get('video')
        if not video:
            return Response(
                {"error": "No video file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        result = {
            "is_fake": False,
            "confidence": 95.5
        }
        
        serializer = self.get_serializer(data={
            'video': video,
            'result': result
        })
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Add this new test view
class S3TestView(APIView):
    """View to test S3 connection"""
    permission_classes = [AllowAny]  # Allow anyone to test for debugging
    
    def get(self, request):
        """Test S3 connection and return bucket details"""
        try:
            # Get settings directly
            from django.conf import settings
            
            # Debug: Print environment variables and settings
            env_bucket = os.environ.get('AWS_STORAGE_BUCKET_NAME')
            env_region = os.environ.get('AWS_S3_REGION_NAME')
            settings_bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'not-set')
            settings_region = getattr(settings, 'AWS_S3_REGION_NAME', 'not-set')
            
            # Create a boto3 session
            session = boto3.session.Session(
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=settings_region  # Use settings value
            )
            
            # Create S3 client
            s3 = session.client('s3')
            
            # Get bucket details
            bucket_name = settings_bucket  # Use settings value
            bucket_exists = True
            
            try:
                s3.head_bucket(Bucket=bucket_name)
            except ClientError as e:
                bucket_exists = False
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                return Response({
                    'connected': False,
                    'bucket_exists': False,
                    'bucket_name': bucket_name,
                    'env_bucket': env_bucket,  # Debug info
                    'env_region': env_region,  # Debug info
                    'settings_bucket': settings_bucket,  # Debug info
                    'settings_region': settings_region,  # Debug info
                    'error_code': error_code,
                    'error_message': error_message
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # List some objects in the bucket (up to 5)
            objects = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
            object_list = []
            
            if 'Contents' in objects:
                for obj in objects['Contents']:
                    object_list.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            return Response({
                'connected': True,
                'bucket_exists': bucket_exists,
                'bucket_name': bucket_name,
                'env_bucket': env_bucket,  # Debug info
                'env_region': env_region,  # Debug info
                'settings_bucket': settings_bucket,  # Debug info
                'settings_region': settings_region,  # Debug info
                'region': settings_region,
                'objects': object_list
            })
            
        except Exception as e:
            return Response({
                'connected': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VideoUploadTestView(APIView):
    """Test view for uploading videos to S3"""
    permission_classes = [IsAuthenticated]  # Allow only authenticated users
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, *args, **kwargs):
        """Handle video upload and storage in S3"""
        logger = logging.getLogger(__name__)
        video_file = request.FILES.get('video')
        run_detection = request.data.get('detect_deepfake', 'true').lower() == 'true'  # Default to true
        
        logger.info(f"Video upload request received, detect_deepfake={run_detection}")
        
        if not video_file:
            logger.error("No video file provided in request")
            return Response({'error': 'No video file provided'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Check file size limit (5MB)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if video_file.size > max_size:
            logger.error(f"Video file too large: {video_file.size} bytes (max: {max_size} bytes)")
            return Response(
                {'error': f'File is too large. Maximum size is 5MB. Your file: {video_file.size/1024/1024:.2f}MB'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Got video file: {video_file.name}, size: {video_file.size} bytes")
        
        try:
            # Use the currently authenticated user
            user = request.user
            logger.info(f"Processing upload for user: {user.username}")
            
            # Get video metadata using FFprobe
            logger.info("Extracting video metadata...")
            video_metadata = self.get_video_metadata(video_file)
            logger.info(f"Video metadata: {video_metadata}")
            
            # Check video duration limit (30 seconds)
            max_duration = 30  # seconds
            duration = video_metadata.get('duration', 0)
            if duration > max_duration:
                logger.error(f"Video duration too long: {duration} seconds (max: {max_duration} seconds)")
                return Response(
                    {'error': f'Video is too long. Maximum duration is {max_duration} seconds. Your video: {duration} seconds'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create a proper Video object instead of just an Analysis
            logger.info("Creating Video object...")
            video = Video(
                User_id=user,
                Video_File=video_file,
                size=video_file.size,
                Length=video_metadata.get('duration', 0),
                Resolution=video_metadata.get('resolution', '0x0'),
                Frame_per_Second=video_metadata.get('fps', 0)
            )
            
            # Save the video (this will trigger the save method that generates thumbnail)
            logger.info("Saving video...")
            video.save()
            logger.info(f"Video saved successfully with ID: {video.Video_id}")
            
            # Store thumbnail URL and video details for response
            thumbnail_url = video.Thumbnail.url if video.Thumbnail else None
            video_details = {
                'resolution': video.Resolution,
                'duration': video.Length,
                'fps': video.Frame_per_Second,
                'size': video.size
            }
            
            # Initialize detection info with default values
            detection_info = {
                "is_fake": False,
                "confidence": 0.0,
                "face_count": 0,
                "processed_frames": 0,
                "detection_time": 0.0,
                "model_used": "No Detection Run"
            }
            
            # Reset file pointer for reading
            video_file.seek(0)
            
            # If detection was requested, run deepfake detection
            if run_detection:
                try:
                    logger.info("Running deepfake detection...")
                    detection, is_fake, confidence, metadata = detect_deepfake(video)
                    
                    detection_info = {
                        "is_fake": is_fake,
                        "confidence": confidence,
                        "face_count": metadata.get("processed_faces", 0),
                        "processed_frames": metadata.get("processed_frames", 0),
                        "detection_time": metadata.get("detection_time", 0.0),
                        "result": 'fake' if is_fake else 'real',
                        "model_used": metadata.get("model_used", "EfficientNet-B1 + LSTM")
                    }
                    logger.info(f"Detection completed: {detection_info}")
                    
                except Exception as e:
                    logger.error(f"Deepfake detection failed: {str(e)}", exc_info=True)
                    # Keep default detection info on error
                    detection_info["error"] = str(e)
            else:
                logger.info("Deepfake detection not requested")
            
            # Create an analysis entry with properly formatted result data
            result_data = {
                "video_id": video.Video_id,
                "is_fake": detection_info.get("is_fake", False),
                "confidence": detection_info.get("confidence", 0.0),
                "detection": detection_info,
                "duration": video_metadata.get('duration', 0)
            }
            
            logger.info(f"Creating analysis with result data: {result_data}")
            
            # IMPORTANT CHANGE: Don't store the video file again in Analysis
            # The video is already saved to S3 when we saved the Video object
            # Instead, create Analysis with reference to video_id
            analysis = Analysis(
                user=user,
                # Don't store video file again - this was causing RAM to increase
                # video=video_file,  # This will be stored in S3
                # Instead, use a direct reference:
                # (Note: If Analysis model has a required video field,
                # you may need to modify the model to include a video_reference field
                # referencing the Video model)
                result=json.dumps(result_data)
            )
            
            # Save the analysis
            analysis.save()
            logger.info(f"Analysis created with ID: {analysis.id}")
            
            # Close the file handle to release memory - the file is already saved to S3
            video_file.close()
            video_file = None
            
            # Force garbage collection
            import gc
            gc.collect()
            
            return Response({
                'success': True,
                'message': 'Video uploaded successfully',
                'analysis_id': analysis.id,
                'video_id': video.Video_id,
                'video_path': video.Video_Path,
                'thumbnail_path': thumbnail_url,
                'video_details': video_details,
                'detection_result': detection_info
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error in VideoUploadTestView: {str(e)}", exc_info=True)
            # Clean up video file from memory
            if video_file:
                video_file.close()
                video_file = None
                import gc
                gc.collect()
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_video_metadata(self, video_file):
        """Extract metadata from video file"""
        metadata = {
            'duration': 0,
            'resolution': '0x0',
            'fps': 0
        }
        
        try:
            # Create a temporary file for FFprobe to analyze
            temp_file_path = None
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(video_file.name)[1], delete=False) as temp_file:
                # Save the uploaded file to the temporary file in chunks to reduce memory usage
                temp_file_path = temp_file.name
                chunk_size = 1024 * 1024  # Process in 1MB chunks
                for chunk in video_file.chunks(chunk_size):
                    temp_file.write(chunk)
                    # Clear chunk from memory
                    chunk = None
                    # Periodically collect garbage
                    if chunk_size % 5 == 0:
                        import gc
                        gc.collect()
                temp_file.flush()
            
            # Use FFprobe to extract metadata
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,r_frame_rate,duration',
                '-of', 'json',
                temp_file_path
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                probe_data = json.loads(result.stdout)
                
                # Extract metadata
                if 'streams' in probe_data and len(probe_data['streams']) > 0:
                    stream = probe_data['streams'][0]
                    
                    # Get resolution
                    width = stream.get('width', 0)
                    height = stream.get('height', 0)
                    metadata['resolution'] = f"{width}x{height}"
                    
                    # Get duration
                    if 'duration' in stream:
                        metadata['duration'] = int(float(stream['duration']))
                    
                    # Get FPS (frame rate)
                    if 'r_frame_rate' in stream:
                        frame_rate = stream['r_frame_rate']
                        if '/' in frame_rate:
                            num, den = frame_rate.split('/')
                            metadata['fps'] = int(float(num) / float(den))
                        else:
                            metadata['fps'] = int(float(frame_rate))
            except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
                print(f"Error extracting metadata: {e}")
                # Use some default values
                metadata = {
                    'duration': 10,
                    'resolution': '640x480',
                    'fps': 30
                }
            finally:
                # Clear result variables
                result = None
                probe_data = None
                
                # Clean up temporary file
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except Exception as e:
                        print(f"Error deleting temp file: {e}")
            
            # Reset file pointer for further processing
            video_file.seek(0)
            
            # Force garbage collection
            import gc
            gc.collect()
            
        except Exception as e:
            print(f"Error in metadata extraction: {e}")
            # Use default values
            metadata = {
                'duration': 10,
                'resolution': '640x480',
                'fps': 30
            }
        
        return metadata

# Add VideoViewSet to show videos in dashboard
class VideoViewSet(viewsets.ModelViewSet):
    """API endpoint to view and manage videos"""
    queryset = Video.objects.all().order_by('-Uploaded_at')
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        """Pass request to serializer for absolute URL generation"""
        context = super().get_serializer_context()
        return context
    
    def get_queryset(self):
        """Filter videos to only show those belonging to the current user"""
        return Video.objects.filter(User_id=self.request.user).order_by('-Uploaded_at')
        
    def list(self, request, *args, **kwargs):
        """Override list to print debugging information"""
        queryset = self.get_queryset()
        print(f"Found {queryset.count()} videos for user {request.user.username}")
        
        serializer = self.get_serializer(queryset, many=True)
        for video_data in serializer.data:
            print(f"Video {video_data['Video_id']} thumbnail: {video_data.get('thumbnail_url')}")
        
        return Response(serializer.data)

class S3SignedURLView(APIView):
    """Generate a signed URL for accessing S3 objects"""
    permission_classes = [AllowAny]  # Allow anyone to access for debugging
    
    def get(self, request):
        """Generate a signed URL for the given S3 key"""
        s3_key = request.query_params.get('key')
        
        if not s3_key:
            return Response({
                'error': 'Missing S3 key parameter'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Create a boto3 session
            session = boto3.session.Session(
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=os.environ.get('AWS_S3_REGION_NAME', 'us-west-2')
            )
            
            s3_client = session.client('s3')
            
            # Get the bucket name
            bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'true-vision')
            
            # Generate a signed URL that lasts for 3600 seconds (1 hour)
            signed_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=3600
            )
            
            return Response({
                'signed_url': signed_url,
                'expires_in': 3600,
                'original_key': s3_key
            })
            
        except ClientError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class S3ImageProxyView(APIView):
    """Proxy endpoint for S3 images to avoid CORS issues"""
    permission_classes = [AllowAny]  # Allow anyone to access images
    
    def get(self, request):
        """Proxy requests to S3 and return the image data"""
        url = request.GET.get('url')
        if not url:
            return Response({'error': 'URL parameter is required'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Extract key and video ID if this is an S3 URL
            key = None
            video_id = None
            
            if 'amazonaws.com' in url:
                # Parse S3 URL to get key
                parts = url.split('amazonaws.com/')
                if len(parts) > 1:
                    key = parts[1].split('?')[0]  # Remove query params
                    
                    # Try to extract video ID from the key
                    match = key.lower().split('/')[-1].split('_')
                    if len(match) > 1 and match[1].isdigit():
                        video_id = match[1].split('.')[0]  # Remove file extension
            
            # Get a signed URL for the requested resource
            signed_url = None
            if key:
                try:
                    # Create S3 client
                    s3_client = boto3.client(
                        's3',
                        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                        region_name=settings.AWS_S3_REGION_NAME
                    )
                    
                    # Check if the object exists
                    try:
                        s3_client.head_object(
                            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                            Key=key
                        )
                        # Object exists, generate signed URL
                        signed_url = s3_client.generate_presigned_url(
                            'get_object',
                            Params={
                                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                'Key': key
                            },
                            ExpiresIn=300  # URL valid for 5 minutes
                        )
                    except ClientError as e:
                        # Object doesn't exist, try fallbacks if we have a video ID
                        if video_id:
                            # Try different possible thumbnail/placeholder keys
                            fallback_keys = [
                                f"media/thumbnails/placeholder_{video_id}.jpg",
                                f"media/thumbnails/thumbnail_{video_id}.jpg",
                                f"media/thumbnails/video_{video_id}.jpg",
                                f"media/videos/thumbnail_{video_id}.jpg"
                            ]
                            
                            for fallback_key in fallback_keys:
                                try:
                                    # Check if this fallback exists
                                    s3_client.head_object(
                                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                        Key=fallback_key
                                    )
                                    # Found a working fallback
                                    signed_url = s3_client.generate_presigned_url(
                                        'get_object',
                                        Params={
                                            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                            'Key': fallback_key
                                        },
                                        ExpiresIn=300
                                    )
                                    break
                                except ClientError:
                                    continue
                        
                        if not signed_url:
                            # If still no valid URL, return generic placeholder
                            return self.serve_placeholder_image()
                except Exception as s3_error:
                    print(f"S3 client error: {str(s3_error)}")
                    return self.serve_placeholder_image()
            
            # Use the original URL if no signed URL was generated
            url_to_fetch = signed_url if signed_url else url
            
            # Make request to the URL with stream=True to avoid loading entire content into memory
            response = requests.get(url_to_fetch, stream=True)
            
            # Check if request was successful
            if response.status_code != 200:
                # If not successful, serve placeholder
                return self.serve_placeholder_image()
            
            # Determine content type
            content_type = response.headers.get('Content-Type')
            if not content_type:
                # Try to guess content type from URL if not provided
                content_type, _ = mimetypes.guess_type(url)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Create Django StreamingHttpResponse to avoid keeping the entire image in memory
            
            # Use a generator function to yield chunks and clean up resources
            def stream_and_cleanup():
                try:
                    # Stream content in small chunks
                    for chunk in response.iter_content(chunk_size=8192):
                        yield chunk
                finally:
                    # Always close the response and clear references
                    response.close()
                    # Force garbage collection
                    import gc
                    gc.collect()
            
            # Create streaming response
            django_response = StreamingHttpResponse(
                stream_and_cleanup(),
                content_type=content_type
            )
            
            # Set Content-Length if available
            if 'Content-Length' in response.headers:
                django_response['Content-Length'] = response.headers['Content-Length']
            
            # Add cache headers
            django_response['Cache-Control'] = 'max-age=86400'  # Cache for 24 hours
            
            return django_response
            
        except Exception as e:
            print(f"Proxy error: {str(e)}")
            return self.serve_placeholder_image()
    
    def serve_placeholder_image(self):
        """Serve a generic placeholder image"""
        try:
            # Try to fetch a placeholder from a public URL
            placeholder_url = "https://placehold.co/600x400?text=No+Image+Found"
            response = requests.get(placeholder_url, stream=True)
            
            if response.status_code == 200:
                # Use StreamingHttpResponse for the placeholder too
                from django.http import StreamingHttpResponse
                
                # Stream content with cleanup
                def stream_placeholder():
                    try:
                        for chunk in response.iter_content(chunk_size=8192):
                            yield chunk
                    finally:
                        response.close()
                        import gc
                        gc.collect()
                
                django_response = StreamingHttpResponse(
                    stream_placeholder(),
                    content_type=response.headers.get('Content-Type', 'image/png')
                )
                
                # Set Content-Length if available
                if 'Content-Length' in response.headers:
                    django_response['Content-Length'] = response.headers['Content-Length']
                
                django_response['Cache-Control'] = 'max-age=86400'
                return django_response
            
            # If that fails, create a simple text response
            return Response(
                {"error": "Image not found and placeholder failed"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as placeholder_error:
            return Response(
                {"error": f"Failed to serve placeholder: {str(placeholder_error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Ensure cleanup
            import gc
            gc.collect()

class S3ObjectExistsView(APIView):
    """Check if an S3 object exists without downloading it"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Check if the specified S3 key exists"""
        key = request.GET.get('key')
        if not key:
            return Response({'error': 'Key parameter is required'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=settings.AWS_S3_REGION_NAME
            )
            
            # Check if the object exists
            exists = True
            alternate_key = None
            
            try:
                s3_client.head_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=key
                )
            except ClientError:
                exists = False
                
                # Check if this is a thumbnail/placeholder and try to find alternatives
                if '/thumbnails/' in key:
                    # Try to extract video ID
                    filename = key.split('/')[-1]
                    match = filename.split('_')
                    if len(match) > 1 and match[1].isdigit():
                        video_id = match[1].split('.')[0]
                        
                        # Check for alternates
                        alternates = [
                            f"media/thumbnails/placeholder_{video_id}.jpg",
                            f"media/thumbnails/thumbnail_{video_id}.jpg",
                            f"media/thumbnails/video_{video_id}.jpg"
                        ]
                        
                        for alt_key in alternates:
                            if alt_key != key:  # Skip the original key
                                try:
                                    s3_client.head_object(
                                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                        Key=alt_key
                                    )
                                    # Found an alternate
                                    alternate_key = alt_key
                                    break
                                except ClientError:
                                    continue
            
            # Generate a signed URL if requested and the object exists
            signed_url = None
            if exists or alternate_key:
                final_key = alternate_key if alternate_key else key
                signed_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': final_key
                    },
                    ExpiresIn=300  # URL valid for 5 minutes
                )
            
            return Response({
                'exists': exists,
                'key': key,
                'alternate_key': alternate_key,
                'signed_url': signed_url
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeepFakeDetectionView(APIView):
    """API endpoint for deepfake detection"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, *args, **kwargs):
        """Process a video for deepfake detection"""
        logger = logging.getLogger(__name__)
        logger.info("DeepFakeDetectionView.post called")
        
        video_file = request.FILES.get('video')
        video_id = request.data.get('video_id')
        
        # Check if we have either a file or a valid video ID
        if not video_file and not video_id:
            logger.error("No video file or video_id provided")
            return Response({
                'error': 'Either video file or video_id must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the video object
            video = None
            
            if video_id:
                # Use existing video
                try:
                    logger.info(f"Using existing video with ID: {video_id}")
                    video = Video.objects.get(Video_id=video_id, User_id=request.user)
                except Video.DoesNotExist:
                    logger.error(f"Video with ID {video_id} not found or access denied")
                    return Response({
                        'error': 'Video not found or access denied'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Upload a new video
                user = request.user
                logger.info(f"Uploading new video for user: {user.username}")
                
                # Get video metadata
                video_metadata = self._get_video_metadata(video_file)
                logger.info(f"Video metadata: {video_metadata}")
                
                # Create video object
                video = Video(
                    User_id=user,
                    Video_File=video_file,
                    size=video_file.size,
                    Length=video_metadata.get('duration', 0),
                    Resolution=video_metadata.get('resolution', '0x0'),
                    Frame_per_Second=video_metadata.get('fps', 0)
                )
                video.save()
                logger.info(f"New video created with ID: {video.Video_id}")
                
                # Reset file pointer
                if video_file:
                    video_file.seek(0)
            
            # Store thumbnail URL for response
            thumbnail_url = video.Thumbnail.url if video.Thumbnail else None
            
            # Process the video with our deepfake detector
            try:
                logger.info(f"Starting deepfake detection for video ID: {video.Video_id}")
                detection, is_fake, confidence, metadata = detect_deepfake(video)
                logger.info(f"Detection completed: is_fake={is_fake}, confidence={confidence}")
                logger.info(f"Detection metadata: {metadata}")
                
                # Format detection result for response
                detection_info = {
                    "is_fake": is_fake,
                    "confidence": confidence,
                    "face_count": metadata.get("processed_faces", 0),
                    "processed_frames": metadata.get("processed_frames", 0),
                    "detection_time": metadata.get("detection_time", 0.0),
                    "result": 'fake' if is_fake else 'real',
                    "model_used": metadata.get("model_used", "EfficientNet-B1 + LSTM")
                }
                
                # Create an analysis entry with properly formatted result data
                result_data = {
                    "video_id": video.Video_id,
                    "is_fake": is_fake,
                    "confidence": confidence,
                    "detection": detection_info
                }
                
                logger.info(f"Creating analysis with result data: {result_data}")
                
                # Create new Analysis object WITHOUT duplicate video storage
                analysis = Analysis(
                    user=request.user,
                    # Don't store video file again - avoids RAM usage duplication
                    # video=video_file if video_file else None,
                    result=json.dumps(result_data)
                )
                analysis.save()
                logger.info(f"Analysis created with ID: {analysis.id}")
                
                # Get video details for response
                video_details = {
                    'resolution': video.Resolution,
                    'duration': video.Length,
                    'fps': video.Frame_per_Second,
                    'size': video.size
                }
                
                # Release file handle to free memory - the file is already saved to S3
                if video_file:
                    video_file.close()
                    video_file = None
                    
                # Force garbage collection
                import gc
                gc.collect()
                
                # Return the results
                return Response({
                    'success': True,
                    'video_id': video.Video_id,
                    'detection': detection_info,
                    'video_details': video_details,
                    'thumbnail_url': thumbnail_url
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                # If deepfake detection fails, log error and return informative message
                logger.error(f"Deepfake detection failed: {str(e)}", exc_info=True)
                # Clean up video file from memory
                if video_file:
                    video_file.close()
                    video_file = None
                    import gc
                    gc.collect()
                return Response({
                    'success': False,
                    'error': f"Deepfake detection failed: {str(e)}",
                    'video_id': video.Video_id,
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(f"Error in DeepFakeDetectionView: {str(e)}", exc_info=True)
            # Clean up video file from memory
            if video_file:
                video_file.close()
                video_file = None
                import gc
                gc.collect()
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_video_metadata(self, video_file):
        """Extract metadata from video file (optimized for memory usage)"""
        metadata = {
            'duration': 0,
            'resolution': '0x0',
            'fps': 0
        }
        
        try:
            # Create a temporary file for FFprobe to analyze
            temp_file_path = None
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(video_file.name)[1], delete=False) as temp_file:
                # Save the uploaded file to the temporary file in chunks to reduce memory usage
                temp_file_path = temp_file.name
                chunk_size = 1024 * 1024  # Process in 1MB chunks
                for chunk in video_file.chunks(chunk_size):
                    temp_file.write(chunk)
                    # Clear chunk from memory
                    chunk = None
                    # Periodically collect garbage
                    if chunk_size % 5 == 0:
                        import gc
                        gc.collect()
                temp_file.flush()
            
            # Use FFprobe to extract metadata
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,r_frame_rate,duration',
                '-of', 'json',
                temp_file_path
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                probe_data = json.loads(result.stdout)
                
                # Extract metadata
                if 'streams' in probe_data and len(probe_data['streams']) > 0:
                    stream = probe_data['streams'][0]
                    
                    # Get resolution
                    width = stream.get('width', 0)
                    height = stream.get('height', 0)
                    metadata['resolution'] = f"{width}x{height}"
                    
                    # Get duration
                    if 'duration' in stream:
                        metadata['duration'] = int(float(stream['duration']))
                    
                    # Get FPS (frame rate)
                    if 'r_frame_rate' in stream:
                        frame_rate = stream['r_frame_rate']
                        if '/' in frame_rate:
                            num, den = frame_rate.split('/')
                            metadata['fps'] = int(float(num) / float(den))
                        else:
                            metadata['fps'] = int(float(frame_rate))
            except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
                print(f"Error extracting metadata: {e}")
                # Use some default values
                metadata = {
                    'duration': 10,
                    'resolution': '640x480',
                    'fps': 30
                }
            finally:
                # Clear result variables
                result = None
                probe_data = None
                
                # Clean up temporary file
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except Exception as e:
                        print(f"Error deleting temp file: {e}")
                        
            # Reset file pointer for further processing
            video_file.seek(0)
            
            # Force garbage collection
            import gc
            gc.collect()
            
        except Exception as e:
            print(f"Error in metadata extraction: {e}")
            # Use default values
            metadata = {
                'duration': 10,
                'resolution': '640x480',
                'fps': 30
            }
        
        return metadata

# ... existing code ...

### for account management
class ChangePasswordView(APIView):
    """View for changing user password"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('currentPassword')
        new_password = request.data.get('newPassword')
        confirm_password = request.data.get('confirmPassword')

        # Validate input
        if not all([current_password, new_password, confirm_password]):
            return Response(
                {"error": "All fields are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {"error": "New passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify current password
        user = authenticate(username=request.user.username, password=current_password)
        if not user:
            return Response(
                {"error": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password updated successfully"},
            status=status.HTTP_200_OK
        )

class DeleteAccountView(APIView):
    """View for deleting user account"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get('password')

        if not password:
            return Response(
                {"error": "Password is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify password
        user = authenticate(username=request.user.username, password=password)
        if not user:
            return Response(
                {"error": "Incorrect password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete user account
        user.delete()

        return Response(
            {"message": "Account deleted successfully"},
            status=status.HTTP_200_OK
        )

class UserInfoView(APIView):
    """View for retrieving user information"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "email": user.email
        })

class ForgotPasswordView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        email = request.data.get('email')
        logger = logging.getLogger(__name__)
        logger.info(f"Forgot password request received for email: {email}")
        
        try:
            user = User.objects.get(email=email)
            logger.info(f"User found with email: {email}")
            
            # Generate PIN
            pin = user.generate_reset_pin()
            logger.info(f"Generated reset PIN for user: {email}")
            
            # Get the correct from email from settings
            from django.conf import settings
            from_email = settings.DEFAULT_FROM_EMAIL
            
            # Create HTML email template with the logo and styling
            html_message = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>True Vision Password Reset</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .logo-title {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #2563eb;
                        margin-bottom: 10px;
                    }}
                    .content {{
                        background-color: #f9f9f9;
                        border-radius: 8px;
                        padding: 30px;
                        margin-bottom: 20px;
                        border: 1px solid #eee;
                    }}
                    .pin {{
                        font-size: 28px;
                        font-weight: bold;
                        text-align: center;
                        color: #2563eb;
                        padding: 10px;
                        margin: 20px 0;
                        letter-spacing: 5px;
                    }}
                    .footer {{
                        font-size: 12px;
                        text-align: center;
                        color: #666;
                        margin-top: 30px;
                    }}
                    .button {{
                        display: inline-block;
                        background-color: #2563eb;
                        color: white;
                        text-decoration: none;
                        padding: 10px 20px;
                        border-radius: 4px;
                        margin-top: 20px;
                    }}
                    .expires {{
                        color: #e53e3e;
                        font-style: italic;
                        margin-top: 15px;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <!-- You can add the logo image here -->
                    <div class="logo-title">TRUE VISION</div>
                    <h2>Password Reset</h2>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>We received a request to reset your password for your True Vision account. Please use the following PIN to verify your identity:</p>
                    <div class="pin">{user.reset_password_pin}</div>
                    <p class="expires">This PIN will expire in 10 minutes.</p>
                    <p>If you did not request this password reset, please ignore this email or contact support if you have concerns about your account security.</p>
                    <p>Thank you,<br>The True Vision Team</p>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} True Vision. All rights reserved.</p>
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </body>
            </html>
            '''
            
            # Plain text version as fallback
            text_message = f"Your True Vision password reset PIN is {user.reset_password_pin}. It is valid for 10 minutes."
            
            # Send email with the PIN
            try:
                from django.core.mail import EmailMultiAlternatives
                
                # Create email message with both HTML and text versions
                email_message = EmailMultiAlternatives(
                    'True Vision Password Reset',
                    text_message,
                    from_email,
                    [user.email]
                )
                email_message.attach_alternative(html_message, "text/html")
                email_message.send()
                
                logger.info(f"Password reset PIN email sent to: {email} from {from_email}")
                return Response({"message": "PIN sent to your email"}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Failed to send email to {email}: {str(e)}")
                return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except User.DoesNotExist:
            logger.warning(f"User with email {email} not found")
            return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)

class ResetPasswordView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        email = request.data.get('email')
        pin = request.data.get('pin')
        new_password = request.data.get('new_password')
        
        logger = logging.getLogger(__name__)
        logger.info(f"Password reset request received for email: {email}")
        
        if not email or not pin or not new_password:
            logger.warning("Missing required parameters for password reset")
            return Response({"error": "Email, PIN, and new password are all required"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            logger.info(f"User found for reset password: {email}")
            
            # Check if the PIN is valid
            if user.is_reset_pin_valid(pin):
                logger.info(f"Valid PIN for user: {email}")
                
                # Set the new password
                try:
                    user.set_password(new_password)
                    logger.info(f"Password changed for user: {email}")
                    
                    # Clear the PIN
                    user.clear_reset_pin()
                    logger.info(f"Reset PIN cleared for user: {email}")
                    
                    # Save the user
                    user.save()
                    logger.info(f"User saved successfully: {email}")
                    
                    return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
                except Exception as e:
                    logger.error(f"Error setting password for {email}: {str(e)}")
                    return Response({"error": f"Failed to set new password: {str(e)}"}, 
                                  status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # Log why the PIN is invalid (expired or incorrect)
                if user.reset_password_pin is None:
                    logger.warning(f"No PIN set for user: {email}")
                    reason = "No PIN has been set for this user"
                elif user.reset_password_pin != pin:
                    logger.warning(f"Incorrect PIN provided for user: {email}")
                    reason = "Incorrect PIN"
                elif user.reset_password_pin_expiration and timezone.now() > user.reset_password_pin_expiration:
                    logger.warning(f"Expired PIN for user: {email}")
                    reason = "PIN has expired"
                else:
                    logger.warning(f"Unknown PIN validation issue for user: {email}")
                    reason = "Invalid PIN"
                
                return Response({"error": f"{reason}"}, 
                              status=status.HTTP_400_BAD_REQUEST)
                
        except User.DoesNotExist:
            logger.warning(f"User with email {email} not found")
            return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)

class TestEmailView(APIView):
    """
    Endpoint to test email sending functionality
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        logger = logging.getLogger(__name__)
        email = request.data.get('email')
        
        if not email:
            return Response({"error": "Email address is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Test email request received for: {email}")
        
        try:
            # Get email settings from Django settings
            from django.conf import settings
            from_email = settings.DEFAULT_FROM_EMAIL
            email_host = settings.EMAIL_HOST
            email_port = settings.EMAIL_PORT
            email_use_tls = settings.EMAIL_USE_TLS
            
            # Log email settings (excluding password)
            logger.info(f"Email settings: HOST={email_host}, PORT={email_port}, TLS={email_use_tls}, FROM={from_email}")
            
            # Find user by email
            try:
                user = User.objects.get(email=email)
                recipient_email = user.email
                logger.info(f"User found with email: {email}")
            except User.DoesNotExist:
                # If user doesn't exist, just use the provided email
                recipient_email = email
                logger.info(f"No user found with email: {email}, using provided email for test")
                
            # Send test email
            send_mail(
                'Test Email from True Vision',
                'This is a test email to verify email sending functionality is working correctly.',
                from_email,  # Use the correct from_email from settings
                [recipient_email],
                fail_silently=False,
            )
            
            logger.info(f"Test email sent successfully to: {recipient_email}")
            
            return Response({
                "message": "Test email sent successfully",
                "settings": {
                    "host": email_host,
                    "port": email_port,
                    "use_tls": email_use_tls,
                    "from_email": from_email
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to send test email: {str(e)}")
            return Response({"error": f"Failed to send test email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




'''from django.shortcuts import render
from api.models import User
from rest_framework.views import APIView
from rest_framework import generics
from .serializers import UserSerializer, NoteSerializer, OperatorAuthorizeSerializer,OperatorSerializer, ParkingSpotsMapSerializer, ParkingSpotSerializer, MapReportSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Note
from rest_framework.response import Response
from rest_framework import status
from .models import ParkingSpotsMap, ParkingSpot, VirtualSensor, MapReport
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, MapAuthorizeSerializer
from rest_framework import status as rest_status



class NoteListCreate(generics.ListCreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Note.objects.filter(author=user)

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(author=self.request.user)
        else:
            print(serializer.errors)


class NoteDelete(generics.DestroyAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Note.objects.filter(author=user)


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class UnapprovedOperatorsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        operators = User.objects.filter(role="operator", authorized=False)
        serializer = OperatorSerializer(operators, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AuthorizeOperatorView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, operator_id):
        if request.user.role != "admin":
            return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            operator = User.objects.get(id=operator_id, role="operator")
        except User.DoesNotExist:
            return Response({"detail": "Operator not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = OperatorAuthorizeSerializer(operator, data={"authorized": True}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RejectOperatorView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, operator_id):
        # Check if the user is an admin
        if request.user.role != "admin":
            return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        # Attempt to retrieve the operator
        try:
            operator = User.objects.get(id=operator_id, role="operator")
        except User.DoesNotExist:
            return Response({"detail": "Operator not found"}, status=status.HTTP_404_NOT_FOUND)

        # Delete the operator from the database
        operator.delete()
        return Response({"detail": "Operator deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


####################################################################
class UnapprovedMapsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        maps = ParkingSpotsMap.objects.filter(accepted=False)
        serializer = ParkingSpotsMapSerializer(maps, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AuthorizeMapView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, map_id):
        if request.user.role != "admin":
            return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            map = ParkingSpotsMap.objects.get(id=map_id)
        except map.DoesNotExist:
            return Response({"detail": "Map not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = MapAuthorizeSerializer(map, data={"accepted": True}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#Updated below class to allow operators to delete there maps
class RejectMapView(APIView):
       permission_classes = [IsAuthenticated]

       def delete(self, request, map_id):
           # Check if the user is an admin or operator
           if request.user.role not in ["admin", "operator"]:
               return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

           # Attempt to retrieve the map
           try:
               map = ParkingSpotsMap.objects.get(id=map_id)
           except ParkingSpotsMap.DoesNotExist:
               return Response({"detail": "Map not found"}, status=status.HTTP_404_NOT_FOUND)

           # Delete the map from the database
           map.delete()
           return Response({"detail": "Map deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class AllAuthorizedMapsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        maps = ParkingSpotsMap.objects.filter(accepted=True)
        serializer = ParkingSpotsMapSerializer(maps, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

####################################################################
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    
    
class AllAuthorizedOperatorsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        operators = User.objects.filter(role="operator", authorized=True)
        serializer = OperatorSerializer(operators, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)




class CreateParkingSpotsMapView(APIView):
    def post(self, request):
        if request.user.is_authenticated and request.user.role == 'operator':
            name= request.data.get('name')
            length = request.data.get('length')
            width = request.data.get('width')
            orientation = request.data.get('orientation')
            loc = request.data.get('loc')
            
            parking_map = ParkingSpotsMap.objects.create(
                operator=request.user,
                name=name,
                length=length,
                width=width,
                orientation=orientation,
                org=request.user.organization,
                email=request.user.email,
                loc = loc
            )
            
            # Automatically generate parking spots and sensors
            for x in range(width):
                for y in range(length):
                    spot = ParkingSpot.objects.create(
                        parking_spots_map=parking_map,
                        x_axis=x,
                        y_axis=y,
                        sensor_status='unused'
                    )
                    VirtualSensor.objects.create(parking_spot=spot)
                    
            return Response({"detail": "ParkingSpotsMap created and spots generated"}, status=status.HTTP_201_CREATED)
        return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

class ParkingSpotsMapView(APIView):
    def get(self, request, operator_id):
        try:
            parking_map = ParkingSpotsMap.objects.filter( operator_id=operator_id)
            pS=ParkingSpotsMapSerializer(parking_map, many=True)
            return Response(pS.data)
        except ParkingSpotsMap.DoesNotExist:
            return Response({"detail": "Map not found"}, status=status.HTTP_404_NOT_FOUND)


class FlipParkingSpotStatusView2(APIView):
    def post(self, request, pk):
        try:
            # Retrieve the parking spot by its ID
            parking_spot = ParkingSpot.objects.get(pk=pk)

            # Define the cycle of statuses
            status_cycle = ['sensor', 'maintenance', 'unavailable', 'road']

            # Get the current index of the status
            current_index = status_cycle.index(parking_spot.status)

            # Flip to the next status
            new_index = (current_index + 1) % len(status_cycle)  # Ensure it loops back to the start
            parking_spot.status = status_cycle[new_index]
            parking_spot.save()

            # Serialize the updated parking spot and return the response
            serializer = ParkingSpotSerializer(parking_spot)
            return Response(serializer.data, status=rest_status.HTTP_200_OK)

        except ParkingSpot.DoesNotExist:
            return Response({"error": "Parking spot not found."}, status=rest_status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=rest_status.HTTP_400_BAD_REQUEST)
        

class ParkingSpotsView(APIView):
    permission_classes = [AllowAny]  # Allow public access

    def get(self, request, map_id):
        spots = ParkingSpot.objects.filter(parking_spots_map_id=map_id)
        serializer = ParkingSpotSerializer(spots, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class FlipParkingSpotStatusView(APIView):
    def patch(self, request, spot_id):
        try:
            spot = ParkingSpot.objects.get(id=spot_id)
        except ParkingSpot.DoesNotExist:
            return Response({"detail": "Parking spot not found"}, status=status.HTTP_404_NOT_FOUND)

        # Define the status flipping logic
        status_order = ["sensor", "maintenance", "unavailable", "road"]
        current_index = status_order.index(spot.status)
        new_status = status_order[(current_index + 1) % len(status_order)]

        spot.status = new_status
        spot.save()
        serializer = ParkingSpotSerializer(spot)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
from .models import Operator
from django.core.mail import send_mail

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            
            user.generate_pin()
            
            # Send email with the PIN
            send_mail(
                'Password Reset PIN',
                f'Your PIN is {user.pin}. It is valid for 10 minutes.',
                'no-reply@example.com',
                [user.email],
                fail_silently=False,
            )
            return Response({"message": "PIN sent to your email"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)
        #except Operator.DoesNotExist:
         #   return Response({"error": "Operator not found"}, status=status.HTTP_404_NOT_FOUND)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        pin = request.data.get('pin')
        new_password = request.data.get('new_password')
        
        try:
            user = User.objects.get(email=email)
            
            if user.pin_is_valid(pin):
                user.set_password(new_password)
                user.save()
                return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid or expired PIN"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)
        #except Operator.DoesNotExist:
          #  return Response({"error": "Operator not found"}, status=status.HTTP_404_NOT_FOUND)


class UpdatePhoneNumberView(APIView):
    def put(self, request):
        user = request.user
        phone_number = request.data.get("phone_number")
        
        if phone_number:
            user.phone_number = phone_number  # assuming phone_number is in Profile model
            user.save()
            return Response({"message": "Phone number updated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Phone number not provided"}, status=status.HTTP_400_BAD_REQUEST)

class CreateMapReportView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = MapReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetMapReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, map_id):
        if request.user.role != 'operator':
            return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        
        reports = MapReport.objects.filter(parking_map_id=map_id).order_by('-created_at')
        serializer = MapReportSerializer(reports, many=True)
        return Response(serializer.data)

#A guest view
class OrganizationsView(APIView):
    permission_classes = [AllowAny]  
    #maps = ParkingSpotsMap.objects.filter(accepted=True)
    def get(self, request):
        
        organizations = ParkingSpotsMap.objects.filter(accepted=True)  
        serializer = ParkingSpotsMapSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DeleteMapReportView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, report_id):
        if request.user.role != 'operator':
            return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            report = MapReport.objects.get(id=report_id)
            report.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MapReport.DoesNotExist:
            return Response({"detail": "Report not found"}, status=status.HTTP_404_NOT_FOUND)


            '''

