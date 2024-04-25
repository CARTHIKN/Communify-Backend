from .models import Room, Message, User
from rest_framework import serializers



class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"




class Userserializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [ 'username']