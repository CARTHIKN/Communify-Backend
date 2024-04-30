from .models import Room, Message, User
from rest_framework import serializers



class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"




class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        
class Userserializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [ 'username']

class MessageSerializer(serializers.ModelSerializer):
    user = Userserializer()  # Using the modified UserSerializer to include only the username

    class Meta:
        model = Message
        fields = ("id", "room", "user", "content", "timestamp", "seen", "m_type")
        read_only_fields = ("id", "timestamp")