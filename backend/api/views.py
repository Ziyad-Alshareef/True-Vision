from rest_framework import status
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .models import Analysis, Video, Model, Detection, DetectionModel, CustomUser
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
from django.http import HttpResponse
import mimetypes

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

# Also create a simple view to test uploading a video
class VideoUploadTestView(APIView):
    """Test view for uploading videos to S3"""
    permission_classes = [IsAuthenticated]  # Allow only authenticated users
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, *args, **kwargs):
        """Handle video upload and storage in S3"""
        video_file = request.FILES.get('video')
        
        if not video_file:
            return Response({'error': 'No video file provided'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Use the currently authenticated user
            user = request.user
            
            # Get video metadata using FFprobe
            video_metadata = self.get_video_metadata(video_file)
            
            # Create a proper Video object instead of just an Analysis
            video = Video(
                User_id=user,
                Video_File=video_file,
                size=video_file.size,
                Length=video_metadata.get('duration', 0),
                Resolution=video_metadata.get('resolution', '0x0'),
                Frame_per_Second=video_metadata.get('fps', 0)
            )
            
            # Save the video (this will trigger the save method that generates thumbnail)
            video.save()
            
            # Also create an analysis entry
            analysis = Analysis(
                user=user,
                video=video_file,
                result=json.dumps({
                    "is_fake": False,
                    "confidence": 95.5,
                    "video_id": video.Video_id
                })
            )
            
            # Save the analysis
            analysis.save()
            
            return Response({
                'success': True,
                'message': 'Video uploaded successfully',
                'analysis_id': analysis.id,
                'video_id': video.Video_id,
                'video_path': video.Video_Path,
                'thumbnail_path': video.Thumbnail.url if video.Thumbnail else None,
                'video_details': {
                    'resolution': video.Resolution,
                    'duration': video.Length,
                    'fps': video.Frame_per_Second,
                    'size': video.size
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
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
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(video_file.name)[1], delete=False) as temp_file:
                # Save the uploaded file to the temporary file
                for chunk in video_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
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
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            # Reset file pointer for further processing
            video_file.seek(0)
            
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
            
            # Make request to the URL
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
            
            # Create Django response with streamed content
            django_response = HttpResponse(
                response.iter_content(chunk_size=1024),
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
                django_response = HttpResponse(
                    response.iter_content(chunk_size=1024),
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

