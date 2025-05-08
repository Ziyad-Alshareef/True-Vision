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

# Get the user model (now points to CustomUser)
User = get_user_model()

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                {"message": "User created successfully"},
                status=status.HTTP_201_CREATED
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
        
        logger.info(f"Got video file: {video_file.name}, size: {video_file.size} bytes")
        
        try:
            # Use the currently authenticated user
            user = request.user
            logger.info(f"Processing upload for user: {user.username}")
            
            # Get video metadata using FFprobe
            logger.info("Extracting video metadata...")
            video_metadata = self.get_video_metadata(video_file)
            logger.info(f"Video metadata: {video_metadata}")
            
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
                "detection": detection_info
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
    permission_classes = [AllowAny]
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
            
            # Send email with the PIN
            try:
                send_mail(
                    'Password Reset PIN',
                    f'Your PIN is {user.reset_password_pin}. It is valid for 10 minutes.',
                    from_email,
                    [user.email],
                    fail_silently=False,
                )
                logger.info(f"Password reset PIN email sent to: {email} from {from_email}")
                return Response({"message": "PIN sent to your email"}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Failed to send email to {email}: {str(e)}")
                return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except User.DoesNotExist:
            logger.warning(f"User with email {email} not found")
            return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        pin = request.data.get('pin')
        new_password = request.data.get('new_password')
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_reset_pin_valid(pin):
                user.set_password(new_password)
                user.clear_reset_pin()  # Clear the PIN after successful reset
                user.save()
                return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid or expired PIN"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
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
            
            # Send test email
            send_mail(
                'Test Email from True Vision',
                'This is a test email to verify email sending functionality is working correctly.',
                from_email,
                [email],
                fail_silently=False,
            )
            
            logger.info(f"Test email sent successfully to: {email}")
            
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

