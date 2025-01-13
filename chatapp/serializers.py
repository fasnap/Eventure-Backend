from rest_framework import serializers
from .models import ChatRoom, Message
from authentication.models import AccountUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountUser
        fields = ['id', 'email', 'username', 'user_type']
        
class ChatRoomSerializer(serializers.ModelSerializer):
    attendee=UserSerializer()
    creator=UserSerializer()
    last_message=serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'attendee', 'creator', 'last_message', 'created_at']
    
    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-timestamp').first()
        if last_message:
            return {
                'content': last_message.content,
                'timestamp': last_message.timestamp
            }
        return None
    
class MessageSerializer(serializers.ModelSerializer):
    sender=UserSerializer()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'timestamp', 'status']