import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path,path
from apii.consumers import ChatConsumer


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat.settings')

application = get_asgi_application()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            [
                re_path(r"ws/chat/(?P<room_name>[\w\d]+)/(?P<username>[\w\d]+)/$", ChatConsumer.as_asgi()),
                
            #    re_path(r'ws/chat/(?P<username>\w+)/(?P<roomname>\w+)/$', ChatConsumer.as_asgi()),
            ]
        )
    ),
})