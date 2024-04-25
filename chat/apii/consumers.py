from .models import User,Message,Room
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async



class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None
        self.users = None


    async def connect(self):
    
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        
        self.userr = self.scope["url_route"]["kwargs"]["username"] or "Anonymous"
        if not self.room_name or len(self.room_name) > 100:
            await self.close(code=400)
            return
        
        self.room_group_name = f"chat_{self.room_name}"
        self.room = await self.get_or_create_room()
        self.user = await self.get_or_create_user()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()


    async def disconnect(self, code):
        self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    
    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message = data['message']
        message_obj = await self.create_message(message)

        if message_obj:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type" : "chat_message",
                    "message" : message,
                    "username": message_obj.user.username,
                }
            )


    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        await self.send(text_data=json.dumps(
            {
            "message" : message,
            "username" : username
            }
        ))

    @database_sync_to_async
    def create_message(self, message, m_type="text"):
        try:
            
            user_instance, _ = User.objects.get_or_create(username=self.user.username)

            
            return Message.objects.create(
                room=self.room, content=message, user=user_instance, m_type=m_type
            )
            
        except Exception as e:
            print(f"Error creating message: {e}")
            return None
        


    @database_sync_to_async
    def get_or_create_room(self):
        room, _ = Room.objects.get_or_create(name=self.room_name)
        return room

    @database_sync_to_async
    def get_or_create_user(self):
        userr = User.objects.get_or_create(username=self.userr)
        print(userr)
        print(self.userr)
        user = User.objects.get(username=self.userr)
        print(user)
        return user