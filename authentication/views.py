# api/views.py
import random
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import AccountUser, AttendeeProfile, CreatorProfile
from .serializers import AttendeeProfileSerializer, UserSerializer, VerifyOTPSerializer, CreatorProfileSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.mail import send_mail

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
            if not user.is_active:
                return Response({"error": "Account is inactive. Please contact support."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the password is correct
            if user.check_password(password) and user.is_verified:
                refresh = RefreshToken.for_user(user)

                return Response({
                    'email': user.email,
                    'username': user.username,
                    'user_type': user.user_type,
                    'refreshToken': str(refresh),
                    'accessToken': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)
        
        except AccountUser.DoesNotExist:
            return Response({"error": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)

class AttendeeProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            attendee_profile = AttendeeProfile.objects.get(user=request.user)
            serializer = AttendeeProfileSerializer(attendee_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)    
        except AttendeeProfile.DoesNotExist:
            return Response({"error": "Attendee profile not found."}, status=status.HTTP_404_NOT_FOUND)
    def put(self, request):
        try:
            attendee_profile = AttendeeProfile.objects.get(user=request.user)
            serializer = AttendeeProfileSerializer(attendee_profile, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Attendee profile updated successfully."}, status=status.HTTP_200_OK)
            else:
                print(serializer.errors)  
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AttendeeProfile.DoesNotExist:
            return Response({"error": "Attendee profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
class CreatorAccountSetupView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def get(self, request):
        try:
            creator_profile = CreatorProfile.objects.get(user=request.user)
            serializer=CreatorProfileSerializer(creator_profile, context={'request': request})
            return Response(serializer.data)
            
        except CreatorProfile.DoesNotExist:
            return Response({"error": "Creator profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
    def put(self, request):
        try:
            creator_profile=CreatorProfile.objects.get(user=request.user)
            serializer=CreatorProfileSerializer(creator_profile, data=request.data)
            print("Uploaded document:", request.FILES.get('document_copy'))  # Debugging line to check if file is received
            if serializer.is_valid():
                serializer.save()
                creator_profile.is_setup_submitted=True
                creator_profile.save()
                return Response({"message": "Account setup request sent to admin for verification."}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except CreatorProfile.DoesNotExist:
            return Response({"error": "Creator profile not found."}, status=status.HTTP_404_NOT_FOUND)

class LogoutView(APIView):
    permission_classes=[IsAuthenticated]
    
    def post(self,request):
        try:
            refresh_token=request.data.get('refresh_token')
            token=RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class ForgotPasswordRequestView(APIView):
    def post(self,request):
        email=request.data.get("email")
        try:
            user=AccountUser.objects.get(email=email)
            otp=random.randint(100000,999999)
            user.otp=otp
            user.save()
            print(f"Generated OTP: {otp}")
            send_mail(
                'Password Reset OTP',
                f'Your OTP for password reset is {otp}',
                'testmaildjango27121995@gmail.com',  # Replace with your email
                [user.email],
                fail_silently=False,
            )
            return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)
        
        except AccountUser.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if new_password != confirm_password:
            return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = AccountUser.objects.get(email=email)
            
            if user.otp == int(otp):
                # Reset password and clear OTP
                user.set_password(new_password)
                user.otp = None  # Clear OTP after successful reset
                user.save()
                return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        
        except AccountUser.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

class VerifyOtpViewForgotPassword(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        try:
            user = AccountUser.objects.get(email=email)
            if user.otp == int(otp):
                return Response({"message": "OTP verified."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        except AccountUser.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
