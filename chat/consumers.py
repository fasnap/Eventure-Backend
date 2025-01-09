# import fileinput
# from channels.generic.websocket import AsyncWebsocketConsumer
# import json
# from channels.db import database_sync_to_async
# from . models import ChatGroup, Message
# from django.contrib.auth import get_user_model
# from jose import jwt
# from django.conf import settings
# from urllib.parse import parse_qs

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         query_string = self.scope.get('query_string', b'').decode()
#         query_params = parse_qs(query_string)
        
#         token=query_params.get('token', [None])[0]

#         if not token:
#             await self.close()
#             return

#         try:
#             payload=jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#             user_id=payload.get("user_id")
#             user=await database_sync_to_async(get_user_model().objects.get)(id=user_id)
#             if not user:
#                 await self.close()
#                 return
#             self.scope['user']=user
#         except jwt.ExpiredSignatureError:
#             await self.close()
#             return
#         except jwt.JWTError:
#             await self.close()
#             return
        
#         self.group_id=self.scope['url_route']['kwargs']['group_id']
#         self.group_name = f"group_{self.group_id}"
#         await self.channel_layer.group_add(self.group_name, self.channel_name)
#         await self.accept()
#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)
        
#     async def receive(self, text_data):
#         data=json.loads(text_data)
#         message = data.get('message', '')
#         file = data.get('file', None)

#         user=self.scope['user']
#         if not user.is_authenticated:
#             return
#         User = get_user_model()
#         try:
#             sender = await database_sync_to_async(User.objects.get)(id=user.id)
#         except User.DoesNotExist:
#             # Handle the case where the user does not exist
#             return
        
#         chat_group = await database_sync_to_async(ChatGroup.objects.get)(id=self.group_id)
#         message_obj = Message(group=chat_group, sender=sender, content=message, file=file)
#         await database_sync_to_async(message_obj.save)()
#         await self.channel_layer.group_send(
#             self.group_name,
#             {
#                 'type': 'chat_message',
#                 'message': message,
#                 'file': file,  
#                 'sender': sender.username,
#                 'sender_username': sender.username,
#                 'timestamp': str(message_obj.timestamp)
#             }
#         )
#     # async def chat_message(self, event):
#     #     await self.send(text_data=json.dumps(event))
#     async def chat_message(self, event):
#         await self.send(text_data=json.dumps({
#             "message": event["message"],
#             "sender": event["sender"],
#             "sender_username": event["sender_username"],
#             'timestamp': event['timestamp'],
#             'file':event['file']
#         }))


from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from . models import ChatGroup, Message
from django.contrib.auth import get_user_model
from jose import jwt
from django.conf import settings
from urllib.parse import parse_qs

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        token=query_params.get('token', [None])[0]

        if not token:
            await self.close()
            return

        try:
            payload=jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id=payload.get("user_id")
            user=await database_sync_to_async(get_user_model().objects.get)(id=user_id)
            if not user:
                await self.close()
                return
            self.scope['user']=user
        except jwt.ExpiredSignatureError:
            await self.close()
            return
        except jwt.JWTError:
            await self.close()
            return
        
        self.group_id=self.scope['url_route']['kwargs']['group_id']
        self.group_name = f"group_{self.group_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        
    async def receive(self, text_data):
        data = json.loads(text_data)
        sender_username = data.get('sender_username')
        message_content = data.get('message')
        file_url = data.get('file')
        user=self.scope['user']
        if not user.is_authenticated:
            return
        User = get_user_model()
        try:
            sender = await database_sync_to_async(User.objects.get)(id=user.id)
        except User.DoesNotExist:
            # Handle the case where the user does not exist
            return
        chat_group = await database_sync_to_async(ChatGroup.objects.get)(id=self.group_id)
        message_obj = Message(group=chat_group, sender=sender, content=message_content, file=file_url)
        # Here you should save the message and file to the database
        await database_sync_to_async(message_obj.save)()
    
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'content': message_content,
                'file': file_url,  
                'sender': sender.username,
                'group':chat_group.id,
                'sender_username': sender.username,
                'timestamp': str(message_obj.timestamp)
            }
        )
    async def chat_message(self, event):
        print("Received event:", event) 
        await self.send(text_data=json.dumps({
            "content": event["content"],
            "sender": event["sender"],
            "sender_username": event["sender_username"],
            'timestamp': event['timestamp'],
            'file':event['file'],
        }))
    
# def save_message(group_id, sender, sender_username, message_content, file_url):
#     user = get_user_model().objects.get(username=sender_username)
#     chat_group = ChatGroup.objects.get(id=group_id)
    
#     print("Saving message to chat", file_url)
#     print("Saving message with file URL:", file_url)
#     print("Message content:", message_content)
#     print("Sender username:", sender_username)
     
#     message = Message.objects.create(
#         sender=user,
#         group=chat_group,
#         content=message_content,
#         file=file_url,  # Save the file URL here
#     )
#     print("message is " , message , "message content id is " , message.id)
#     return message