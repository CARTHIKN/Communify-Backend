import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat.settings')

application = get_asgi_application()


from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path,path
from apii.consumers import ChatConsumer


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            [
                re_path(r"ws/chat/(?P<room_name>[\w\d]+)/(?P<username>[\w\d]+)/$", ChatConsumer.as_asgi()),
                
            ]
        )
    ),
})