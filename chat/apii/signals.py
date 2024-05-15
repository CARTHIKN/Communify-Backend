from .models import Message,User,NotificationRoom
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import random
import string


def generate_mixed_string(length=10):
        characters = string.ascii_letters
        mixed_string = "".join(random.choice(characters) for _ in range(length))
        return mixed_string

def create_notification(user,room):
    users_in_room = room.userslist.all()
    other_user = room.userslist.exclude(id=user.id).first()

    if other_user:
        try:
            print("1")
            not_room = NotificationRoom.objects.get(user_id=other_user.id)
            
        except NotificationRoom.DoesNotExist:
            print("2")
            r_name = generate_mixed_string()
            not_room = NotificationRoom.objects.create(user_id=other_user.id, name = r_name)
        room_name = not_room.name
        print(room_name)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_name,
            {
                "type": "send_chat_notification",
                "user": other_user.username,
            }
        )

        print("Notification sent for", other_user.username)
    else:
        print("No other user in the room")