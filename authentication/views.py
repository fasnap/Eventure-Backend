# api/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import AccountUser, CreatorProfile
from .serializers import UserSerializer, VerifyOTPSerializer, CreatorProfileSerializer
from rest_framework.permissions import IsAuthenticated

class UserCreate(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        try:
            user = AccountUser.objects.get(email=email)

            # Check if the password is correct
            if user.check_password(password) and user.is_verified:
                refresh = RefreshToken.for_user(user)

                return Response({
                    'email': user.email,
                    'username': user.username,
                    'user_type': user.user_type,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid email or password, or account not verified."}, status=status.HTTP_400_BAD_REQUEST)
        
        except AccountUser.DoesNotExist:
            return Response({"error": "Invalid email or password, or account not verified."}, status=status.HTTP_400_BAD_REQUEST)
        
class CreatorAccountSetupView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            creator_profile = CreatorProfile.objects.get(user=request.user)
            serializer=CreatorProfileSerializer(creator_profile)
            return Response(serializer.data)
            
        except CreatorProfile.DoesNotExist:
            return Response({"error": "Creator profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
    def post(self, request):
        try:
            creator_profile=CreatorProfile.objects.get(user=request.user)
            serializer=CreatorProfileSerializer(creator_profile, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Account setup request sent to admin for verification."}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except CreatorProfile.DoesNotExist:
            return Response({"error": "Creator profile not found."}, status=status.HTTP_404_NOT_FOUND)