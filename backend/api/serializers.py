'''from api.models import User
from rest_framework import serializers
from .models import Note, MapReport


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'phone_number', 'organization', 'role', 'authorized']
        extra_kwargs = {
            'password': {'write_only': True},  # Ensure password is write-only
            'organization': {'required': False},  # Only required for Operators
            'phone_number': {'required': False},  # Only required for Operators
        }

    def create(self, validated_data):
        print(validated_data)
        user = User.objects.create_user(**validated_data)
        return user


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "title", "content", "created_at", "author"]
        extra_kwargs = {"author": {"read_only": True}}


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom claims (role, organization, etc.)
        data['role'] = self.user.role
        data['authorized'] = self.user.authorized
        if self.user.role == 'operator':
            data['organization'] = self.user.organization

        return data
    


class OperatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'organization', 'email', 'phone_number', 'authorized']

class OperatorAuthorizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['authorized']

    def update(self, instance, validated_data):
        instance.authorized = validated_data.get('authorized', instance.authorized)
        instance.save()
        return instance
    

from rest_framework import serializers
from .models import ParkingSpotsMap, ParkingSpot, VirtualSensor

class ParkingSpotsMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSpotsMap
        fields = '__all__'

class MapAuthorizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSpotsMap
        fields = ['accepted']

    def update(self, instance, validated_data):
        instance.accepted = validated_data.get('accepted', instance.accepted)
        instance.save()
        return instance

class ParkingSpotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSpot
        fields = '__all__'

class VirtualSensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualSensor
        fields = '__all__'

class MapReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapReport
        fields = ['id', 'parking_map', 'text', 'created_at', 
                 'font_size', 'font_family', 'text_align', 
                 'font_weight', 'font_style']
'''
# api/serializers.py

'''
from rest_framework import serializers
from .models import CustomUser, Analysis

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'password', 'email')
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = ('id', 'user', 'video', 'result', 'created_at')
        read_only_fields = ('user', 'created_at')

    '''

from rest_framework import serializers
from .models import Analysis,CustomUser, Video
import json

class AnalysisSerializer(serializers.ModelSerializer):
    result_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Analysis
        fields = ['id', 'user', 'video', 'result_data', 'created_at']
        read_only_fields = ['user', 'created_at']
    
    def get_result_data(self, obj):
        return obj.get_result()

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password']
        
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class VideoSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    upload_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = ['Video_id', 'user', 'video_url', 'thumbnail_url', 'Resolution', 
                  'Length', 'size', 'upload_date', 'isAnalyzed', 'Frame_per_Second']
    
    def get_thumbnail_url(self, obj):
        if obj.Thumbnail:
            # Get the full URL path including domain
            request = self.context.get('request')
            thumbnail_url = None
            
            # First try to get a pre-signed URL for S3
            try:
                import boto3
                from botocore.exceptions import ClientError
                import os
                from django.conf import settings
                
                # Extract the key from the Thumbnail URL
                thumbnail_key = obj.Thumbnail.name
                print(f"Thumbnail key for video {obj.Video_id}: {thumbnail_key}")
                
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
                        'Key': thumbnail_key
                    },
                    ExpiresIn=3600
                )
                
                thumbnail_url = signed_url
                print(f"Generated signed URL for thumbnail {obj.Video_id}: {thumbnail_url}")
                
            except Exception as e:
                print(f"Error generating signed URL for thumbnail {obj.Video_id}: {str(e)}")
                # Fall back to regular URL if signed URL generation fails
                if request is not None and not obj.Thumbnail.url.startswith(('http://', 'https://')):
                    thumbnail_url = request.build_absolute_uri(obj.Thumbnail.url)
                else:
                    thumbnail_url = obj.Thumbnail.url
            
            return thumbnail_url
        return None
    
    def get_video_url(self, obj):
        if obj.Video_File:
            # Get the full URL path
            request = self.context.get('request')
            video_url = None
            
            # First try to get a pre-signed URL for S3
            try:
                import boto3
                from botocore.exceptions import ClientError
                import os
                from django.conf import settings
                
                # Extract the key from the Video File URL
                video_key = obj.Video_File.name
                print(f"Video key for video {obj.Video_id}: {video_key}")
                
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
                        'Key': video_key
                    },
                    ExpiresIn=3600
                )
                
                video_url = signed_url
                print(f"Generated signed URL for video {obj.Video_id}: {video_url}")
                
            except Exception as e:
                print(f"Error generating signed URL for video {obj.Video_id}: {str(e)}")
                # Fall back to regular URL if signed URL generation fails
                if request is not None and not obj.Video_File.url.startswith(('http://', 'https://')):
                    video_url = request.build_absolute_uri(obj.Video_File.url)
                else:
                    video_url = obj.Video_File.url
            
            return video_url
        
        return obj.Video_Path
    
    def get_user(self, obj):
        return obj.User_id.username
    
    def get_upload_date(self, obj):
        return obj.Uploaded_at.strftime('%Y-%m-%d %H:%M')
