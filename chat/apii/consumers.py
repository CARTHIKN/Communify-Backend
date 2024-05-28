from .models import User,Message,Room,NotificationRoom
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
import random
import string
from .signals import create_notification


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
        await self.seen_messages()


   




    async def disconnect(self, code):
        self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    
    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message = data.get("message")
        m_type = data.get("m_type")
    
        message_obj = await self.create_message(message, m_type)

        if message_obj:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type" : "chat_message",
                    "content": message_obj.content,
                    "username": message_obj.user.username,
                    "timestamp": str(message_obj.timestamp),
                    "seen": message_obj.seen,
                    "m_type": message_obj.m_type,
                },
                
            )
        await self.seen_messages()
        


    async def chat_message(self, event):
        message = event['content']
        username = event['username']
        timestamp = event["timestamp"]
        m_type = event["m_type"]


        await self.send(text_data=json.dumps(
            {
            "content" : message,
            "username" : username,
            "timestamp": timestamp,
            "m_type": m_type,
            }
        ))

    @database_sync_to_async
    def create_message(self, message, m_type):
        try:
            
            user_instance, _ = User.objects.get_or_create(username=self.user.username)
            create_notification(user=self.user,room=self.room)

            
            return Message.objects.create(
                room=self.room, content=message, user=user_instance, m_type=m_type
            )
            
        except Exception as e:
            return None
        


    @database_sync_to_async
    def get_or_create_room(self):
        room, _ = Room.objects.get_or_create(name=self.room_name)
        return room

    @database_sync_to_async
    def get_or_create_user(self):
        userr = User.objects.get_or_create(username=self.userr)
        user = User.objects.get(username=self.userr)
        return user
    
    @database_sync_to_async
    def seen_messages(self):
        un_read = Message.objects.filter(room=self.room).exclude(user=self.user)
        for obj in un_read:
            obj.seen = True
            obj.save()
    


class NotificationConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room = None
        self.user = None 
        self.room_group_name = None
        self.data = None
        self.rooms = None

    async def connect(self):
       
        self.userr = self.scope["url_route"]["kwargs"]["username"] or "Anonymous"
        if not self.userr or len(self.userr) > 100:
            await self.close(code=400)
            return
        self.user = await self.get_or_create_user()
        self.room = await self.get_or_create_room()
        self.room_group_name = self.room_name
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        

    async def disconnect(self, close_code):
       await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
       

    async def send_chat_notification(self, event):

        await self.send(
            text_data=json.dumps({"type": "chat_notification", "user": event["user"]})
        )

    async def send_notification(self, event):

        await self.send(
            text_data=json.dumps({"type": "notification", "user": event["user"]})
        )
    

    async def receive(self, text_data):
        # Handle incoming messages if needed
        pass


    def generate_mixed_string(self, length=10):
        characters = string.ascii_letters
        mixed_string = "".join(random.choice(characters) for _ in range(length))
        return mixed_string


    @database_sync_to_async
    def get_or_create_user(self):
        userr = User.objects.get_or_create(username=self.userr)
        user = User.objects.get(username=self.userr)
        return user
    

    @database_sync_to_async
    def get_or_create_room(self):

        try:
            room = NotificationRoom.objects.get(user=self.user)
            self.room_name = room.name
        except:

            self.room_name = self.generate_mixed_string()
            room = NotificationRoom.objects.create(user=self.user, name=self.room_name)
        return room