from django.urls import path 
from . import consumers

websocket_urlpatterns = [
    # Use path() for a simple route match
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]