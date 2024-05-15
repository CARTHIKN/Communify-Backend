from django.db import models
from django.db.models import Max



class User(models.Model):
    username = models.CharField(max_length=255)
    is_online = models.BooleanField(default=False)

    def __str__(self):
        return self.username
    


class Room(models.Model):
    name = models.TextField(max_length=100)
    userslist = models.ManyToManyField(to=User, blank=True)

    @property
    def online(self):
        return self.userslist.filter(is_online=True)
    
    def get_last_message(self):
        last_message = self.messages.aggregate(last_message=Max('timestamp'))['last_message']
        return self.messages.filter(timestamp=last_message).first()



class Message(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, related_name="messages", on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)
    m_type = models.CharField(blank=True)


    class Meta:
        db_table = "chat_message"
        ordering = ("timestamp",)


class NotificationRoom(models.Model):
    name = models.CharField(max_length=40)
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)


   
class Notifications(models.Model):
    user = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    post_id = models.CharField(blank=True, null=True)
    by_user = models.CharField(max_length=255, blank=True, null=True)
    seen = models.BooleanField(default=False)