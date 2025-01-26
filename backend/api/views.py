from django.shortcuts import render
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