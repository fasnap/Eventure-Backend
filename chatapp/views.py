from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from rest_framework.parsers import MultiPartParser, FormParser

class ChatRoomListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user=request.user
        if user.user_type=='attendee':
            chat_rooms=ChatRoom.objects.filter(attendee=user)
        elif user.user_type=='creator':
            chat_rooms=ChatRoom.objects.filter(creator=user)
        
        serializer = ChatRoomSerializer(chat_rooms, many=True)
        return Response(serializer.data)

class ChatMessagesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, room_id):
        try:
            chat_room=ChatRoom.objects.get(id=room_id)
            if request.user not in [chat_room.attendee, chat_room.creator]:
                return Response(
                    {"error": "You are not a participant in this chat room."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            messages=Message.objects.filter(chat_room=chat_room).order_by('timestamp')
            serializer=MessageSerializer(messages, many=True, context={'request': request})
            return Response(serializer.data)
        except ChatRoom.DoesNotExist:
            return Response({"error": "Chat room not found."}, status=status.HTTP_404_NOT_FOUND)
class CreateChatRoomView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        attendee_id=request.data.get('attendee_id')
        creator_id=request.data.get('creator_id')
        
        if not all([attendee_id, creator_id]):
            return Response({"error": "Attendee and creator IDs are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        chat_room=ChatRoom.objects.filter(
            attendee_id=attendee_id,
            creator_id=creator_id
        ).first()
        
        if not chat_room:
            chat_room = ChatRoom.objects.create(
                attendee_id=attendee_id,
                creator_id=creator_id
            )
        serializer = ChatRoomSerializer(chat_room)
        return Response(serializer.data)

