from django.urls import path
from . import views

urlpatterns = [
    path('', views.process_video, name='process_video'),
    path('stop_video_feed', views.stop_video_feed, name='stop-video'),
    path('live_exercise', views.live_exercise, name='live-exercise'),
    path('video', views.video_feed, name='video_feed')
]