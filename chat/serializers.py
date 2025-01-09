
from rest_framework import serializers

from .models import ChatGroup, Message

class ChatGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatGroup
        fields =  ['id', 'name', 'event', 'owner', 'members']
    
class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username') 
    class Meta:
        model = Message
        fields = ['id', 'group', 'sender', 'sender_username', 'content', 'timestamp', 'file']