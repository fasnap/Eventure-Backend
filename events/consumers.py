import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Notification

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
