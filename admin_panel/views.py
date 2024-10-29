from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.serializers import CreatorProfileSerializer
from .serializers import AdminLoginSerializer
from authentication.models import AccountUser, CreatorProfile
from rest_framework.permissions import IsAdminUser

# Create your views here.
class AdminLoginView(APIView):
    def post(self, request):
        serializer=AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            email=serializer.validated_data['email']
            password=serializer.validated_data['password']
            user=AccountUser.objects.filter(email=email, user_type='admin').first()
            if user and user.check_password(password):
                refresh=RefreshToken.for_user(user)
                return Response({
                    'email':user.email,
                    'username':user.username,
                    'refresh':str(refresh),
                    'access':str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            return Response({'error':'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreatorProfileListView(APIView):
    permission_classes=[IsAdminUser]
    
    def get(self, request):
        creators=CreatorProfile.objects.all()
        serializer=CreatorProfileSerializer(creators, many=True)
        return Response(serializer.data)

class CreatorProfileApprovalView(APIView):
    permission_classes=[IsAdminUser]
    def post(self, request, pk):
        try:
            creator_profile=CreatorProfile.objects.get(pk=pk)
            creator_profile.is_verified=True
            creator_profile.save()
            return Response({'message':'Creator profile approved'}, status=status.HTTP_200_OK)
        except CreatorProfile.DoesNotExist:
            return Response({'error':'Creator profile not found'}, status=status.HTTP_404_NOT_FOUND)

class CreatorProfileRejectView(APIView):
    permission_classes=[IsAdminUser]
    def post(self, request, pk):
        try:
            creator_profile=CreatorProfile.objects.get(pk=pk)
            creator_profile.delete()
            return Response({'message':'Creator profile rejected'}, status=status.HTTP_200_OK)
        except CreatorProfile.DoesNotExist:
            return Response({'error':'Creator profile not found'}, status=status.HTTP_404_NOT_FOUND)