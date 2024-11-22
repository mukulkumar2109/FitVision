import cv2
import json
from channels.generic.websocket import WebsocketConsumer
from time import sleep
from pose_processing import poseDetector

class VideoFeedConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.detector = poseDetector()

        self.cap = cv2.VideoCapture(0)

        while self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                break

            frame = self.detector.findPose(frame)

            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            self.send(bytes_data=frame_bytes)

            sleep(0.033)

    def disconnect(self, close_code):
        self.cap.release()
