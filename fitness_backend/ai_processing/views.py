from django.shortcuts import render
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .pose_processing import poseDetector
import os

stop_flag = False

def stop_video():
    global stop_flag
    stop_flag = True

from rest_framework.response import Response
from rest_framework.decorators import api_view
import os
import logging

@api_view(['POST']) 
def process_video(request):
    try:
        
        if 'video' not in request.FILES:
            return Response({'error': 'No video file provided'}, status=400)

        video_file = request.FILES['video']
        exercise = request.data.get('exercise', 'bicep curls').lower()
        body_part = request.data.get('body_part', 'left arm').lower()

        
        video_path = f"/tmp/{video_file.name}"

        
        with open(video_path, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)

       
        result = poseDetector.process_video_frames(video_path, exercise, body_part, lambda: stop_flag)

        
        if os.path.exists(video_path):
            os.remove(video_path)

        
        return Response({'result': result}, status=200)

    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        return Response({'error': 'File not found'}, status=500)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return Response({'error': str(e)}, status=500)



@api_view(['POST'])
def live_exercise(request):
    return HttpResponse("hi")

    # global stop_flag
    # stop_flag = False

    # exercise = request.data.get('exercise', 'bicep curls').lower()
    # body_part = request.data.get('body_part', 'right arm').lower()

    # result = poseDetector.process_video_frames(0, exercise, body_part, lambda: stop_flag)

    # return Response({'result': result})


@api_view(['POST'])
def stop_video_feed(request):
    stop_video()
    return Response({'message': 'Video processing stopped'})

def video_feed(request):
    return render(request, 'home.html')