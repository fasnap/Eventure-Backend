from django.urls import re_path
from .consumers import NotificationConsumer, StreamingConsumer

websocket_urlpatterns = [
    re_path(r'ws/admin/notifications/', NotificationConsumer.as_asgi()),
    re_path(r'ws/stream/(?P<event_id>\w+)/$', StreamingConsumer.as_asgi()),


]
