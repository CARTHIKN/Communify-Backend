from rest_framework import generics
from .serializers import UserSerializer
from .models import User,Room
import random
from rest_framework.response import Response
from .serializers import RoomSerializer
from rest_framework import status
from django.shortcuts import render
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
from datetime import datetime


class Chatroomlist(generics.ListCreateAPIView):
    serializer_class = RoomSerializer

    def post(self, request):
        username = request.data.get("username")
        print(username, "---------------------------------------------------")
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
                    serializer = UserSerializer(userr)
                    users.append(serializer.data)
            print(users)
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
        print(user1_name,user2_name)
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
                print(serializer.data)
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
