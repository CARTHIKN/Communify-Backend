from django.db import models



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