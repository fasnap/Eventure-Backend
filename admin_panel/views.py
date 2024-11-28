from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.serializers import CreatorProfileSerializer, UserSerializer
from .serializers import AdminLoginSerializer
from authentication.models import AccountUser, CreatorProfile
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination

from events.models import Event
from events.serializers import EventSerializer

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
                    'username': user.username,
                    'user_type': user.user_type,
                    'refreshToken': str(refresh),
                    'accessToken': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            return Response({'error':'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreatorProfileListView(APIView):
    permission_classes=[IsAdminUser]
    
    def get(self, request):
        creators=CreatorProfile.objects.filter(is_verified=False, is_setup_submitted=True)
        serializer=CreatorProfileSerializer(creators, many=True, context={'request': request})
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

class ApprovedCreatorsListView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        creators=CreatorProfile.objects.filter(is_verified=True)
        serializer=CreatorProfileSerializer(creators, many=True, context={'request': request})
        return Response(serializer.data)

class UsersListView(APIView):
    permission_classes=[IsAdminUser, IsAuthenticated]
    def get(self,request):
        users=AccountUser.objects.all()
        
        # Filter by user type
        user_type=request.query_params.get("filter")
        if user_type  and user_type.lower() != "all":
            users=users.filter(user_type=user_type.lower())
        
       # Seach by username or email
        search_term=request.query_params.get("search")
        if search_term:
            users=users.filter(Q(username__icontains=search_term) | Q(email__icontains=search_term))
        
        # Sorting by 
        sort_order=request.query_params.get("sort","desc")
        sort_by=request.query_params.get("sort_by", "created_at")
        
        if sort_by == "username":
            sort_field="username" if sort_order == "asc" else "-username"
        elif sort_by == "email":
            sort_field="email" if sort_order == "asc" else "-email"
        else:
            sort_field="created_at" if sort_order == "asc" else "-created_at"

        users=users.order_by(sort_field)
        
        paginator=PageNumberPagination()
        paginator.page_size=10
        result_page=paginator.paginate_queryset(users, request)
        
        serializer=UserSerializer(result_page,many=True)
        return paginator.get_paginated_response(serializer.data)
        
class BlockUnblockUserView(APIView):
    permission_classes=[IsAdminUser, IsAuthenticated]   
    def patch(self,request,user_id):
        try:
            user=AccountUser.objects.get(id=user_id)
            user.is_active=not user.is_active
            user.save()
            return Response({'message':'User status updated'}, status=status.HTTP_200_OK)
        except AccountUser.DoesNotExist:
            return Response({'error':'User not found'}, status=status.HTTP_404_NOT_FOUND)

class EventsListView(APIView):
    permission_classes=[IsAdminUser]
    def get(self,request):
        events=Event.objects.all().order_by('-created_at')
        serializer=EventSerializer(events, many=True)
        return Response(serializer.data)    
                               
class EventApprovalView(APIView):
    permission_classes=[IsAdminUser]
    
    def post(self, request, event_id):
        try:
            event=Event.objects.get(pk=event_id)
            event.is_approved=True
            event.save()
            return Response({'message':'Event approved'}, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({'error':'Event not found'}, status=status.HTTP_404_NOT_FOUND)

class EventRejectView(APIView):
    permission_classes=[IsAdminUser]
    
    def post(self, request, event_id):
        try:
            event=Event.objects.get(pk=event_id)
            event.is_approved=False
            event.save()
            return Response({'message':'Event rejected'}, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({'error':'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        
class ApprovedEventsListView(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        events=Event.objects.filter(is_approved=True)
        serializer=EventSerializer(events, many=True)
        return Response(serializer.data)