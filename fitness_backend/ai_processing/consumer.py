import cv2
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
import json
import numpy as np
from .pose_processing import poseDetector  
import time

class VideoStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.camera = None
        self.is_streaming = False
        self.detector = poseDetector()
        self.exercise = None
        self.body_part = None
        self.count = 0
        self.dir = 0
        self.pTime = time.time()
        self.reps = 0
        self.time_taken = 0
        self.stream_task = None
        logging.info("WebSocket connection accepted.")

    async def disconnect(self, close_code):
        self.is_streaming = False
        if self.stream_task:
            await self.stream_task

        if self.camera:
            self.camera.release()
        logging.info("WebSocket connection closed, camera released.")

    async def receive(self, text_data=None, bytes_data=None):
        logging.info(f"Received data: {text_data}")
        if text_data:
            data = json.loads(text_data)
            command = data.get("command")

            if command == "start":
                self.exercise = data.get("exercise")
                self.body_part = data.get("bodyPart")
                if not self.is_streaming:
                    self.is_streaming = True
                    self.camera = cv2.VideoCapture(0)
                    logging.info(f"Started video streaming for {self.exercise}, {self.body_part}.")
                    self.stream_task = asyncio.create_task(self.stream_video())


            elif command == "stop":
                self.is_streaming = False
                logging.info("Stopping video stream...")
                # Return results (this is just a placeholder)
                if self.stream_task:
                    await self.stream_task
                results = {
                    "reps": self.reps,  # Example value
                    "exercise": self.exercise,
                    "body_part": self.body_part,
                    "time_taken": self.time_taken  # Example value
                }
                await self.send(text_data=json.dumps(results))
                logging.info("results sent")

    async def stream_video(self):
        while self.is_streaming:
            ret, frame = self.camera.read()
            if not ret:
                logging.error("Failed to capture frame.")
                break
            
            processed_frame, self.reps, self.time_taken = self.process_frame(frame)
            logging.info(f"{self.reps}, {self.time_taken}")
            _, buffer = cv2.imencode('.jpg', processed_frame)
            frame_data = buffer.tobytes()

            # Send the frame data to the frontend
            await self.send(bytes_data=frame_data)
            await asyncio.sleep(1 / 30)  # Limit frame rate to ~30 FPS

        if self.camera:
            self.camera.release()
            self.camera = None


    def process_frame(self, frame):
        """
        Process a single frame to detect pose, calculate angle, and count reps.
        """
        frame = self.detector.findPose(frame, draw=False)
        lmList = self.detector.findPosition(frame, draw=False)
        per=None
        if len(lmList) != 0:
            if self.exercise == "bicep curls" and self.body_part in ["right arm", "left arm"]:
                angle = self.detector.findAngle(frame, 12, 14, 16) if self.body_part == "right arm" else self.detector.findAngle(frame, 11, 13, 15)
                if angle > 180:
                    per = np.interp(angle, (210, 310), (0, 100))
                else:
                    per = np.interp(angle, (60, 165), (100, 0))

            elif self.exercise == "bench press" and self.body_part in ["right arm", "left arm"]:
                angle = self.detector.findAngle(frame, 12, 14, 16) if self.body_part == "right arm" else self.detector.findAngle(frame, 11, 13, 15)
                if angle > 160:
                    per = np.interp(angle, (185, 330), (0, 100))
                else:
                    per = np.interp(angle, (50, 150), (0, 100))

            elif self.exercise == "pushups" and self.body_part in ["right arm", "left arm"]:
                angle = self.detector.findAngle(frame, 12, 14, 16) if self.body_part == "right arm" else self.detector.findAngle(frame, 11, 13, 15)
                if angle > 180:
                    per = np.interp(angle, (195, 285), (0, 100))
                else:
                    per = np.interp(angle, (65, 155), (0, 100))

            elif self.exercise == "squats" and self.body_part in ["right leg", "left leg"]:
                angle = self.detector.findAngle(frame, 24, 26, 28) if self.body_part == "right leg" else self.detector.findAngle(frame, 23, 25, 27)
                if angle > 180:
                    per = np.interp(angle, (195, 290), (0, 100))
                else:
                    per = np.interp(angle, (60, 160), (100, 0))

            color = (0, 0, 255)
            if per == 100:
                color = (0, 255, 0)
                if self.dir == 0:
                    self.count += 0.5
                    self.dir = 1
            if per == 0:
                if self.dir == 1:
                    self.count += 0.5
                    self.dir = 0

        cTime = time.time()
        
        return frame, int(self.count), int(cTime - self.pTime)

 