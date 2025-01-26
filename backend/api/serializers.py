from api.models import User
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
