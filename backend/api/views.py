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
    permission_classes = [AllowAny]  # Allow anyone for testing
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, *args, **kwargs):
        """Handle video upload and storage in S3"""
        video_file = request.FILES.get('video')
        
        if not video_file:
            return Response({'error': 'No video file provided'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Instead of creating a new user, get the first user or an admin user
            try:
                # Try to get a superuser first
                user = User.objects.filter(is_superuser=True).first()
                if not user:
                    # If no superuser, get the first user
                    user = User.objects.first()
                if not user:
                    # If no users exist at all, create a fallback error
                    return Response({
                        'success': False,
                        'error': "No users exist in the database to associate with the upload"
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({
                    'success': False,
                    'error': f"Error finding user: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
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
                'thumbnail_path': video.Thumbnail.url if video.Thumbnail else None
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
    
    def get_queryset(self):
        """Filter videos to only show those belonging to the current user"""
        return Video.objects.filter(User_id=self.request.user).order_by('-Uploaded_at')

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

