# api/views.py
import random
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from events.serializers import EventSerializer
from .models import AccountUser, AttendeeProfile, CreatorProfile
from .serializers import AttendeeProfileSerializer, UserSerializer, VerifyOTPSerializer, CreatorProfileSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from events.models import Notification
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from decouple import config
from .tasks import send_otp_email
from events.models import Event
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
class GoogleAuthView(APIView):
    def post(self, request):
        """
        Handles Google Login
        """
        token = request.data.get("token")
        user_type = request.data.get("user_type")
        
        if not token:
            return Response({"error": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)

        if user_type not in ["attendee", "creator"]:
            return Response({"error": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the Google token
            idinfo = id_token.verify_oauth2_token(token, Request(), config('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY'))
            email = idinfo.get("email")
            first_name = idinfo.get("given_name")
            last_name = idinfo.get("family_name")

            username = email.split('@')[0]
            base_username = username
            # Check if the user already exists
            user, created = AccountUser.objects.get_or_create(email=email, defaults={
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'is_verified': True,
                'user_type': user_type,
                'is_active': True
            })
            if user.is_active ==False:
                return Response({"error": "Account is inactive. Please contact support."}, status=status.HTTP_400_BAD_REQUEST)
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            print("user id is ", user.id)
            return Response({
                'user_id': user.id,
                'email': user.email,
                'username': user.username,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": "Invalid Google token."}, status=status.HTTP_400_BAD_REQUEST)
        
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
    print("hii")
    def post(self, request):
        print("hii1")
        email = request.data.get("email")
        password = request.data.get("password")
        print("hii2")
        print("email: ", email, "password: ", password)
        try:
            user = AccountUser.objects.get(email=email)
            if not user.is_active:
                return Response({"error": "Account is inactive. Please contact support."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the password is correct
            if user.check_password(password) and user.is_verified:
                refresh = RefreshToken.for_user(user)
                print("user id is ", user.id)
                return Response({
                    'user_id': user.id,
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
        print("Request")
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
            user=request.user
            creator_profile=CreatorProfile.objects.get(user=request.user)
            # Only allow the creator to modify their own profile or an admin
            if creator_profile.user != request.user and not request.user.is_staff:
                return Response({"error": "You do not have permission to edit this profile."}, status=status.HTTP_403_FORBIDDEN)
            
            serializer=CreatorProfileSerializer(creator_profile, data=request.data)
            if serializer.is_valid():
                serializer.save()
                creator_profile.is_setup_submitted=True
                creator_profile.save()
                channel_layer = get_channel_layer()
                message = f"New creator '{user.username}' is waiting for admin approval."
                # Create a notification in the database for the admin
                notification = Notification.objects.create(
                    user_id=user.id,  # Assuming the admin has an `id`
                    message=message
                )
            
                async_to_sync(channel_layer.group_send)(
                    'admin_notifications',  # The group name
                    {
                        'type': 'send_notification',
                        'message': message,
                        'notification_id': notification.id
                    }
               )
       
                return Response({"message": "Account setup request sent to admin for verification."}, status=status.HTTP_200_OK)
            print("error", serializer.errors)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except CreatorProfile.DoesNotExist:
            print("profile not found")
            return Response({"error": "Creator profile not found."}, status=status.HTTP_404_NOT_FOUND)

class CreatorProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        try:
            creator_profile = CreatorProfile.objects.get(id=id)
            serializer=CreatorProfileSerializer(creator_profile)
            return Response(serializer.data)
            
        except CreatorProfile.DoesNotExist:
            return Response({"error": "Creator profile not found."}, status=status.HTTP_404_NOT_FOUND)

class LogoutView(APIView):
    permission_classes=[IsAuthenticated]
    
    def post(self,request):
        refresh_token=request.data.get('refresh_token')
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
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
            subject = "OTP for Password Reset"
            message = "Your OTP for password reset is "

            send_otp_email.delay(user.email, otp, subject, message)  # Offload email sending to Celery task

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

class CreatorListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        creators=AccountUser.objects.filter(user_type='creator', creatorprofile__is_verified=True, is_verified=True, is_active=True)
        creator_data=[]
        for creator in creators:
            profile=creator.creatorprofile
           
            event_count=Event.objects.filter(creator=creator, admin_status='approved', is_approved=True).count()
            profile_picture_url = (
                request.build_absolute_uri(profile.profile_picture.url)
                if profile.profile_picture and profile.profile_picture.name
                else None
            )
            creator_data.append({
                "id":creator.id,
                "username": creator.username,
                "email": creator.email,
                "organisation_name": profile.organisation_name,
                "profile_picture": profile_picture_url,
                "event_count": event_count,
            })
            print("creator data", creator_data)

        return Response(creator_data, status=status.HTTP_200_OK)

class CreatorDetailsView(APIView):
    def get(self, request, creator_id):
        try:
            creator=AccountUser.objects.get(id=creator_id)
            profile=creator.creatorprofile
            completed_events=Event.objects.filter(creator=creator, creator_status='completed', admin_status='approved', is_approved=True)
            total_completed_events= completed_events.count()
            
            ongoing_events=Event.objects.filter(creator=creator, creator_status='ongoing', admin_status='approved', is_approved=True)
            total_ongoing_events= ongoing_events.count()
            
            upcoming_events=Event.objects.filter(creator=creator, creator_status='upcoming', admin_status='approved', is_approved=True)
            total_upcoming_events= upcoming_events.count()
            
            events_data = EventSerializer(completed_events, many=True).data
            profile_picture_url = (
                request.build_absolute_uri(profile.profile_picture.url)
                if profile.profile_picture and profile.profile_picture.name
                else None
            )
            creator_data={
                "id":creator_id,
                "username": creator.username,
                "email": creator.email,
                "organisation_name": profile.organisation_name,
                "profile_picture": profile_picture_url,
                "events": events_data,
                "total_completed_events":total_completed_events,
                "total_ongoing_events": total_ongoing_events,
                "total_upcoming_events": total_upcoming_events,
                   
            }
            return Response(creator_data, status=status.HTTP_200_OK)
        except AccountUser.DoesNotExist:
            return Response({"error": "Creator not found."}, status=status.HTTP_404_NOT_FOUND)
