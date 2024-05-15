from django.urls import path

from . import views


urlpatterns = [
    
    path("chatrooms/", views.Chatroomlist.as_view(), name="chatrooms"),
    path("findroom/", views.FindRoom.as_view(), name="findroom"),
    path("messages/",views.MessageList.as_view(),name="chat-messages",),
    path('lastmessage/',views.GetLastMessage.as_view(),name="lastmessage"),
    path('mark-messages-as-seen/', views.SeenMessages.as_view(), name='mark_messages_as_seen'),
    path('unseen-messages/', views.get_unseen_messages, name='get_unseen_messages'),
    path('all-unseen-messages/<str:username>/', views.AllRoomUnseenMessagesAPIView.as_view(), name='all-unseen-messages'),
    
    ]