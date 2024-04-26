from django.urls import path

from . import views


urlpatterns = [
    
    path("chatrooms/", views.Chatroomlist.as_view(), name="chatrooms"),
    path("findroom/", views.FindRoom.as_view(), name="findroom"),
     path("messages/",views.MessageList.as_view(),name="chat-messages",),
    
    ]