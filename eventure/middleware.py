from channels.middleware import BaseMiddleware
from jose import jwt
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.conf import settings

class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        print("TokenAuthMiddleware Initialized")
        super().__init__(inner)
    async def decode_token(self, token):
        print("token in middleware", token)
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user = await database_sync_to_async(get_user_model().objects.get)(id=user_id)
            return user
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    async def connect(self, event):
        print("In TokenAuthMiddleware connect method")

        token = self.scope['query_string']
        token = parse_qs(token.decode())['token'][0]  # Get token from query string
        user = await self.decode_token(token)
        
        if user:
            self.scope['user'] = user  # Set user in the WebSocket scope
            return await super().connect(event)
        else:
            await self.close()  # Close WebSocket if token is invalid
            