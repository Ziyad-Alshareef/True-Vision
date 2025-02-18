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
from .models import Analysis,CustomUser
import json

class AnalysisSerializer(serializers.ModelSerializer):
    result = serializers.JSONField()  # This will handle the JSON serialization/deserialization

    class Meta:
        model = Analysis
        fields = ('id', 'user', 'video', 'result', 'created_at')
        read_only_fields = ('user', 'created_at')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Convert the stored string back to JSON when retrieving
        try:
            ret['result'] = json.loads(instance.result)
        except:
            ret['result'] = {}
        return ret

    def to_internal_value(self, data):
        # Convert JSON to string when saving
        if 'result' in data and not isinstance(data['result'], str):
            data = data.copy()
            data['result'] = json.dumps(data['result'])
        return super().to_internal_value(data)
    

    
class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
