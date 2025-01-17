import json
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from .models import AccountUser
from .models import Notification, Event
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async
import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs



class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "admin_notifications"
        # Join room group
       
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        notification_message = data['message']
        user_id = data['user_id']  
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_notification',
                'message': notification_message,
                'notification_id': data['notification_id']
            }
        )

    # Receive message from room group
    async def send_notification(self, event):
        message = event['message']
        notification_id = event.get('notification_id') 
        if notification_id is None:
            print("Error: notification_id not found in event")
            return  # Optionally, handle this case by skipping the message or logging it

        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'notification_id': notification_id
        }))

class StreamingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        self.room_group_name = f"streaming_{self.event_id}"
        print(f"User connecting to room: {self.room_group_name}")
        
        # Extract and validate token
        query_string = parse_qs(self.scope['query_string'].decode())
        token = query_string.get('token', [None])[0]
        
        if not token:
            print("No token provided")
            return await self.close()
        
        self.user = await self.get_user_from_token(token)
        if not self.user:
            print("Invalid token or user not found")
            return await self.close()
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'streaming_signal',
                'message': {
                    'type': 'join',
                    'sender_id': str(self.user.id)
                }
            }
        )
    
    async def disconnect(self, close_code):
        if hasattr(self, 'user'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'streaming_signal',
                    'message': {
                        'type': 'peer_disconnected',
                        'sender_id': str(self.user.id)
                    }
                }
            )
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        print("text data in receive", text_data)
        try:
            data = json.loads(text_data)
            data['sender_id'] = str(self.user.id)
            
            # Forward the signal to the target peer
            target_id = data.get('target')
            if target_id:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'streaming_signal',
                        'message': data,
                        'target_id': target_id
                    }
                )
            else:
                # If no target, broadcast to the entire group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'streaming_signal',
                        'message': data
                    }
                )
        except Exception as e:
            print(f"Error in receive: {str(e)}")
            await self.close()
    
    async def streaming_signal(self, event):
        try:
            target_id = event.get('target_id')
            if target_id:
                # Check if the current connection's user is the target
                if str(self.user.id) == target_id:
                    await self.send(text_data=json.dumps(event['message']))
            else:
                # Broadcast to all connections in the group
                await self.send(text_data=json.dumps(event['message']))
        except Exception as e:
            print(f"Error in streaming_signal: {str(e)}")

    @database_sync_to_async
    def get_user_from_token(self, token):
        from rest_framework_simplejwt.tokens import AccessToken
        try:
            decoded_token = AccessToken(token)
            user_id = decoded_token['user_id']
            User = get_user_model()
            return User.objects.get(id=user_id)
        except Exception as e:
            print(f"Token validation error: {str(e)}")
            return None