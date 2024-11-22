from django.urls import path
from ..fitness_backend import consumers

websocket_urlpatterns = [
    path('/ws/video_feed/', consumers.VideoFeedConsumer.as_asgi()),
]