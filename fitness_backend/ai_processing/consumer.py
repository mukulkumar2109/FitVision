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
        self.a = 200
        self.prev = [0,0]
        self.prev2 = [0,0]
        self.wrist_coords = []
        self.shoulder_coords = []
        self.shoulder_movement = 0
        self.wrist_movement = 300
        self.flag = 0
        self.per=0
        self.bar = 0
        self.color = (0,0,255)
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
                self.disconnect()
                if self.camera:
                    self.camera.release()

    async def stream_video(self):
        while self.is_streaming:
            ret, frame = self.camera.read()
            if not ret:
                logging.error("Failed to capture frame.")
                break
            frame=cv2.resize(frame,(1500,920))
            processed_frame, self.reps, self.time_taken = self.process_frame(frame)
            # logging.info(f"{self.reps}, {self.time_taken}")
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
        if len(lmList) != 0:
            if self.exercise == "bicep curls" and self.body_part in ["right arm", "left arm"]:
                # if (lmList[12][1]<0.5 or lmList[14][1]<0.5 or lmList[16][1] < 0.5):
                #     print("boo")
                # else:
                angle = self.detector.findAngle(frame, 12, 14, 16) if self.body_part == "right arm" else self.detector.findAngle(frame, 11, 13, 15)
                shoulder_landmark = 11 if self.body_part == "left arm" else 12
                wrist_landmark = 15 if self.body_part == "left arm" else 16


                self.shoulder_coords = [lmList[shoulder_landmark][2], lmList[shoulder_landmark][3]]
                # print(f"{lmList[shoulder_landmark][2]} {lmList[shoulder_landmark][3]}")
                self.wrist_coords = [lmList[wrist_landmark][2], lmList[wrist_landmark][3]]
                
                # shoulder_coords = self.detector.findPosition(frame, shoulder_landmark)
                # wrist_coords = self.detector.findPosition(frame, wrist_landmark)
                # print(shoulder_coords)
                self.shoulder_movement = max(abs(self.shoulder_coords[1] - self.prev[1]), abs(self.shoulder_coords[0] - self.prev[0])) 
                
                
                shoulder_movement_threshold = 10
                wrist_movement_threshold = 300
                
                self.prev = self.shoulder_coords
                if(self.shoulder_movement>shoulder_movement_threshold or self.wrist_movement<wrist_movement_threshold):
                    print(f"You are not preforming {self.exercise}. Should we move to a different exercise?")
                else:
                    if angle > 180:
                        self.per = np.interp(angle, (210, 310), (0, 100))
                        self.bar = np.interp(angle, (210,310), (850,300))
                    else:
                        self.per = np.interp(angle, (60, 165), (100, 0))
                        self.bar = np.interp(angle, (60,165), (300,850))

                self.color = (0, 0, 255)
                if self.per == 100:
                    self.color = (0, 255, 0)
                    if self.dir == 0:
                        self.count += 0.5
                        self.dir = 1
                        if(self.flag == 1):
                            self.wrist_movement = max(abs(self.wrist_coords[-1] - self.prev2[1]), abs(self.wrist_coords[-2] - self.prev2[0])) 
                            self.prev2[0]=self.wrist_coords[-2]
                            self.prev2[1]=self.wrist_coords[-1]
                            print(self.wrist_movement)
                            self.flag = 0
                if self.per == 0:
                    if self.dir == 1:
                        self.count += 0.5
                        self.dir = 0
                        if(self.flag==0):
                            self.wrist_movement = max(abs(self.wrist_coords[1] - self.prev2[1]), abs(self.wrist_coords[0] - self.prev2[0])) 
                            self.prev2[0]=self.wrist_coords[-2]
                            self.prev2[1]=self.wrist_coords[-1]
                            print(self.wrist_movement)
                            self.flag = 1
                    
                    

            elif self.exercise == "bench press" and self.body_part in ["right arm", "left arm"]:
                angle = self.detector.findAngle(frame, 12, 14, 16) if self.body_part == "right arm" else self.detector.findAngle(frame, 11, 13, 15)
                if angle > 160:
                    self.per = np.interp(angle, (185, 330), (0, 100))
                    self.bar = np.interp(angle, (185,330), (650,100))
                else:
                    self.per = np.interp(angle, (50, 150), (0, 100))
                    self.bar = np.interp(angle, (50,150), (650,100))

            elif self.exercise == "pushups" and self.body_part in ["right arm", "left arm"]:
                angle = self.detector.findAngle(frame, 12, 14, 16) if self.body_part == "right arm" else self.detector.findAngle(frame, 11, 13, 15)
                if angle > 180:
                    self.per = np.interp(angle, (195, 285), (0, 100))
                    self.bar = np.interp(angle, (195,285), (850,100))
                else:
                    self.per = np.interp(angle, (65, 155), (0, 100))
                    self.bar = np.interp(angle, (65,155), (850,100))

            elif self.exercise == "squats" and self.body_part in ["right leg", "left leg"]:
                if self.body_part == "right leg":
                    angle = self.detector.findAngle(frame, 24, 26, 28) 
                elif self.body_part == "left leg":
                    self.detector.findAngle(frame, 23, 25, 27)
                if angle > 180:
                    self.per = np.interp(angle, (195, 290), (0, 100))
                    self.bar = np.interp(angle, (195,290), (650,100))
                else:
                    self.per = np.interp(angle, (60, 160), (100, 0))
                    self.bar = np.interp(angle, (60,160), (100,650))

            elif self.exercise == "dips" and self.body_part in ["right arm", "left arm"]:
                if self.body_part == "right arm":
                    angle = self.detector.findAngle(frame, 12, 14, 16) 
                    self.per = np.interp(angle, (85,170), (100, 0))
                    self.bar = np.interp(angle, (85,170), (100,650))
                else:
                    self.detector.findAngle(frame, 11, 13, 15)
                    self.per = np.interp(angle, (190,250),(0,100))
                    self.bar = np.interp(angle, (190,250), (650,100))

            elif self.exercise=="crunches":
                angle = self.detector.findAngle(frame,12,24,26)
                self.per = np.interp(angle, (108,120),(0,100))
                self.bar = np.interp(angle, (108,120), (650,100))

            
        
        if(self.count>9.5):
            self.a=300
        cv2.rectangle(frame,(1350,300),(1425,850),(255,255,255),3)
        cv2.rectangle(frame,(1350,int(self.bar)),(1425,850),self.color,cv2.FILLED)
        cv2.putText(frame, f'{int(self.per)}%', (1350,275), cv2.FONT_HERSHEY_PLAIN, 4, (255,0,0), 4)

        cv2.rectangle(frame,(0,700),(self.a,920),(0,255,0),cv2.FILLED)
        cv2.putText(frame, str(int(self.count)), (45,870), cv2.FONT_HERSHEY_PLAIN, 10, (0,0,255), 15)
        
        cTime = time.time()
        
        cv2.putText(frame,f'Time: {int(cTime-self.pTime)}s', (60,140), cv2.FONT_HERSHEY_DUPLEX, 1, (255,255,255), 2)

        fps = 1/(cTime-self.pTime)
        pTime=cTime
        cv2.putText(frame, "fps: "+ str(int(fps)), (55,90), cv2.FONT_HERSHEY_PLAIN, 3, (250,0,0), 2)
        cv2.putText(frame, str(int(angle)), (0,360), cv2.FONT_HERSHEY_PLAIN, 4, (0,0,255), 4)
        
        return frame, int(self.count), int(cTime - self.pTime)

 