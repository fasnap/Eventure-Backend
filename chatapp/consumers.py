import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message
from authentication.models import AccountUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        query_string=self.scope['query_string'].decode()
        token=dict(x.split('=') for x in query_string.split('&')).get('token', '')
        
        user=await self.get_user_from_token(token)
        if not user:
            await self.close()
            return
        self.user=user
        
        await self.channel_layer.group_add(
            self.room_group_name, 
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, 
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            
            if message_type == 'message':
                message = text_data_json.get('message')
                if not message:
                    raise ValueError("Message content is required")
                    
                chat_message = await self.save_message(message)
                
                await self.channel_layer.group_send(
                    self.room_group_name, 
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender_id': self.user.id,
                        'message_id': chat_message.id,
                        'timestamp': chat_message.timestamp.isoformat(),
                        'status': 'sent'
                    }
                )
           
            elif message_type == 'message_read':
                message_id = text_data_json.get('message_id')
                if not message_id:
                    raise ValueError("Message ID is required")
                    
                await self.update_message_status(message_id,'read')
                await self.channel_layer.group_send(
                    self.room_group_name, 
                    {
                       'type':'message_status_update',
                       'message_id': message_id,
                       'status':'read',
                    }
                )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except ValueError as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': 'An unexpected error occurred'
            }))
            
    async def message_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'status_update',
           'message_id': event['message_id'],
           'status': event['status'],
        }))
    
    @database_sync_to_async
    def update_message_status(self, message_id, status):
        message=Message.objects.get(id=message_id)
        message.status=status
        message.save()
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
           'message': event['message'],
           'sender_id': event['sender_id'],
           'message_id': event['message_id'],
           'timestamp': event['timestamp'],
           'status': event['status'],
           'sender': {
               'id': self.user.id,
               'username': self.user.username
           }
        }))
        
    @database_sync_to_async
    def save_message(self, message):
        chat_room=ChatRoom.objects.get(id=self.room_id)
        return Message.objects.create(
            chat_room=chat_room,
            sender=self.user,
            content=message,
        )
        
    @database_sync_to_async
    def get_user_from_token(self, token):
        from rest_framework_simplejwt.tokens import AccessToken
        try:
            decoded_token=AccessToken(token)
            user_id=decoded_token['user_id']
            return AccountUser.objects.get(id=user_id)
        except Exception:
            return None
        
        