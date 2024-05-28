from rest_framework import generics
from .serializers import UserSerializer
from .models import User,Room
import random
from rest_framework.response import Response
from .serializers import RoomSerializer
from rest_framework import status
from django.shortcuts import get_object_or_404, render
from .models import Message, Room, User
from .serializers import RoomSerializer, UserSerializer,Userserializer, MessageSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
import json
from django.db.models import Q
import random
import string
from django.http import JsonResponse
from time import timezone
from rest_framework.decorators import api_view
from datetime import datetime


class Chatroomlist(generics.ListCreateAPIView):
    serializer_class = RoomSerializer

    def post(self, request):
        username = request.data.get("username")
        try:
            user = User.objects.get(username=username)
            queryset = Room.objects.filter(userslist__in=[user.id])
            serializer = RoomSerializer(queryset, many=True)
            userslist = [
                user_id for room in serializer.data for user_id in room["userslist"]
            ]
          
            users = []
            userslist_values = list(set(userslist))
            for x in userslist_values:
                if x != user.id:
                    userr = User.objects.get(id=x)
                    userr2 = User.objects.get(id=user.id)
                    for room in Room.objects.all():
                        if userr in room.userslist.all() and userr2 in room.userslist.all():
                            serializer = UserSerializer(userr)
                            user_data = serializer.data
                            user_data['room_id'] = room.id
                            users.append(user_data)

        
            return Response(data=users, status=status.HTTP_200_OK)
        except:
            return Response(
                data={"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST
            )



class FindRoom(APIView):
    def generate_mixed_string(self, length=5):
        characters = string.digits + string.ascii_letters 
        mixed_string = ''.join(random.choice(characters) for _ in range(length))
        return mixed_string

    def get_or_create_user(self, username):
        user, created = User.objects.get_or_create(username=username)
        return user

    def get_or_create_room(self, user1, user2):
        room_name = self.generate_mixed_string()
        room, created = Room.objects.get_or_create(name=room_name)
        room.userslist.add(user1, user2)
        return room
    

    def get(self, request):
        user1_name = request.query_params.get("user1")
        user2_name = request.query_params.get("user2")
        if user1_name and user2_name:
            try:
                user1 = self.get_or_create_user(user1_name)
                user2 = self.get_or_create_user(user2_name)

                user1_rooms = Room.objects.filter(userslist=user1)
                user2_rooms = Room.objects.filter(userslist=user2)

                room = user1_rooms.filter(userslist=user2).first()

                if not room: 
                    room = self.get_or_create_room(user1, user2)

                serializer = RoomSerializer(room)
               
                return Response(data=serializer.data, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class MessageList(APIView):
    def get(self, request):
        try:
            room = request.query_params.get("room")
            messages = Message.objects.filter(room__name=room).order_by("timestamp")
            serializer = MessageSerializer(messages, many=True)
            return Response(data=serializer.data, status=status.HTTP_202_ACCEPTED)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

class GetLastMessage(APIView):

    def get(self,request):
        
        room_id = request.GET.get('roomid')  # Use request.GET to get query parameters

        try:
            last_message = Message.objects.filter(room=room_id).order_by("-timestamp")[:1]
            m = last_message[0]
            serializer = MessageSerializer(m)
            return Response(data=serializer.data,status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
        


class SeenMessages(APIView):

    def post(self, request, *args, **kwargs):
        # Assuming you are sending room_name and username from the frontend
        room_name = request.data.get('room_name')
        username = request.data.get('username')
        
        # Get the room object
        room = get_object_or_404(Room, name=room_name)
        
        # Get the user object based on the username
        user = get_object_or_404(User, username=username)
        
        # Get unread messages for the room excluding the current user
        un_read = Message.objects.filter(room=room).exclude(user=user)
        
        # Mark unread messages as seen
        for obj in un_read:
            obj.seen = True
            obj.save()
        
        return Response("Messages marked as seen", status=status.HTTP_200_OK)

@api_view(['GET'])
def get_unseen_messages(request):
    
    if request.method == 'GET':
        

        room_id = request.query_params.get('roomid')
        username = request.query_params.get('username')
        userr = User.objects.get(username=username)
        if room_id and username:
            room = get_object_or_404(Room, id=room_id)
            unseen_messages = Message.objects.filter(room=room, seen=False).exclude(user=userr).count()
            return Response({'count': unseen_messages}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Room ID or Username not provided'}, status=status.HTTP_400_BAD_REQUEST)

class AllRoomUnseenMessagesAPIView(APIView):
    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": f"User with username {username} does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        
        rooms = user.room_set.all()
        all_unseen_messages = []

        for room in rooms:
           
            room_messages = room.messages.exclude(user=user, )
            unseen_messages = room_messages.filter(seen=False)
            all_unseen_messages.extend(unseen_messages)
        
        count = len(all_unseen_messages)
        
        return Response(count, status=status.HTTP_200_OK)
