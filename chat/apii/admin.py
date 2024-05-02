from django.contrib import admin
from .models import User, Message, Room

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username')  # Include 'id' in the list display

class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'content', 'room', 'timestamp')  # Include 'id' in the list display

class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')  # Include 'id' in the list display

# Register your models with the custom admin classes
admin.site.register(User, UserAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Room, RoomAdmin)
