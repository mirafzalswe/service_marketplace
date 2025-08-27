import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = await self.get_user_from_token()
        
        if self.user and self.user.is_authenticated:
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            
            self.role_group = f"role_{self.user.role}"
            await self.channel_layer.group_add(self.role_group, self.channel_name)
            
            await self.accept()
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to notifications'
            }))
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if hasattr(self, 'role_group'):
            await self.channel_layer.group_discard(self.role_group, self.channel_name)

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")


    async def order_notification(self, event):
        await self.send(text_data=json.dumps(event))

    async def payment_notification(self, event):
        await self.send(text_data=json.dumps(event))

    async def status_update(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_user_from_token(self):
        try:

            token = None
            query_string = self.scope.get('query_string', b'').decode()
            if query_string:
                for param in query_string.split('&'):
                    key, value = param.split('=') if '=' in param else (param, '')
                    if key == 'token':
                        token = value
                        break
            
            if not token:
                return AnonymousUser()
            
            UntypedToken(token)
            
            from rest_framework_simplejwt.authentication import JWTAuthentication
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            
            return user
        except (InvalidToken, TokenError, Exception) as e:
            logger.error(f"Token validation error: {e}")
            return AnonymousUser()