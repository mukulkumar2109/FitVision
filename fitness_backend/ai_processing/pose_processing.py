import cv2
import mediapipe as mp
import numpy as np
import math
import time

class poseDetector:
    def __init__(self, mode=False, model_compx=1, smooth=True, seg=False, smooth_seg=True, detectionConf=0.5, trackConf=0.5):
        self.mode = mode
        self.model_compx = model_compx
        self.smooth = smooth
        self.seg = seg
        self.smooth_seg = smooth_seg
        self.detectionConf = detectionConf
        self.trackConf = trackConf

        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(self.mode, self.model_compx, self.smooth, self.seg, self.smooth_seg, self.detectionConf, self.trackConf)

        

    def findPose(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        if self.results.pose_landmarks:
            if draw:
                self.mpDraw.draw_landmarks(img, self.results.pose_landmarks, self.mpPose.POSE_CONNECTIONS)
        return img
    
    def findPosition(self, img, draw=True):
        self.lmList = []
        if self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x*w), int(lm.y*h)
                self.lmList.append([id,lm.visibility, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 3, (255, 0, 0), cv2.FILLED)
        return self.lmList
    
    def findAngle(self, img, p1, p2, p3, draw=True):
        x1, y1 = self.lmList[p1][2:]
        x2, y2 = self.lmList[p2][2:]
        x3, y3 = self.lmList[p3][2:]

        angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1-x2))
        if angle < 0:
            angle += 360

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
            cv2.line(img, (x3, y3), (x2, y2), (0, 255, 0), 3)
            cv2.circle(img, (x1, y1), 7, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 7, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x3, y3), 7, (0, 0, 255), cv2.FILLED)

        return angle
    
    def process_video_frames(video_path, exercise, body_part, stop_flag):
        prev = [0,0]
        prev2 = [0,0]
        wrist_coords = []
        shoulder_coords = []
        shoulder_movement = 0
        wrist_movement = 300
        flag = 0
        per=0
        bar = 0

        cap = cv2.VideoCapture(video_path)
        detector = poseDetector()
        count = 0
        dir = 0
        results = {
            "reps": 0,
            "exercise": exercise,
            "body_part": body_part,
            "time_taken": 0,
            "messages": ""
        }
        warning_sent = False

        pTime = time.time()
        while True:
            success, img = cap.read()
            if not success:
                break

            img = detector.findPose(img, draw=False)
            lmList = detector.findPosition(img, draw=False)

            if len(lmList) != 0:
                if exercise == "bicep curls" and body_part in ["right arm", "left arm"]:
                    angle = detector.findAngle(img, 12, 14, 16) if body_part == "right arm" else detector.findAngle(img, 11, 13, 15)
                    shoulder_landmark = 11 if body_part == "left arm" else 12
                    wrist_landmark = 15 if body_part == "left arm" else 16

                    shoulder_landmark = 11 if body_part == "left arm" else 12
                    wrist_landmark = 15 if body_part == "left arm" else 16

                    shoulder_coords = [lmList[shoulder_landmark][2], lmList[shoulder_landmark][3]]
                    # print(f"{lmList[shoulder_landmark][2]} {lmList[shoulder_landmark][3]}")
                    wrist_coords = [lmList[wrist_landmark][2], lmList[wrist_landmark][3]]
                    # print(f"sh {wrist_coords}")
                    # print(f"prev {prev}")
                    shoulder_movement = max(abs(shoulder_coords[1] - prev[1]), abs(shoulder_coords[0] - prev[0])) 
                    # print(shoulder_movement)
                    
                    shoulder_movement_threshold = 10
                    wrist_movement_threshold = 100
                    
                    prev = shoulder_coords
                    if(shoulder_movement>shoulder_movement_threshold or wrist_movement<wrist_movement_threshold):
                        if not warning_sent:
                            warning = f"You are not preforming {exercise}. Should we move to a different exercise?"
                            results["messages"] = warning
                            warning_sent=True
                    else:
                        if angle > 180:
                            per = np.interp(angle, (210, 310), (0, 100))
                        else:
                            per = np.interp(angle, (60, 165), (100, 0))

                elif exercise == "bench press" and body_part in ["right arm", "left arm"]:
                    angle = detector.findAngle(img, 12, 14, 16) if body_part == "right arm" else detector.findAngle(img, 11, 13, 15)
                    if angle > 160:
                        per = np.interp(angle, (185,330),(0,100))
                    else:
                        per = np.interp(angle, (50,150),(0,100))


                elif exercise == "pushups" and body_part in ["right arm", "left arm"]:
                    angle = detector.findAngle(img, 12, 14, 16) if body_part == "right arm" else detector.findAngle(img, 11, 13, 15)
                    if angle > 180:
                        per = np.interp(angle, (195,285),(0,100))
                    else:
                        per = np.interp(angle, (65,155),(0,100))

                elif exercise == "squats" and body_part in ["right leg", "left leg"]:
                    angle = detector.findAngle(img, 24, 26, 28) if body_part == "right leg" else detector.findAngle(img, 23, 25, 27)
                    if angle > 180:
                        per = np.interp(angle, (195,290),(0,100))
                    else:
                        per = np.interp(angle, (60,160),(100,0))

                color = (0, 0, 255)
                if per == 100:
                    color = (0, 255, 0)
                    if dir == 0:
                        count += 0.5
                        dir = 1
                        if(flag == 1):
                            wrist_movement = max(abs(wrist_coords[-1] - prev2[1]), abs(wrist_coords[-2] - prev2[0])) 
                            prev2[0]=wrist_coords[-2]
                            prev2[1]=wrist_coords[-1]
                            print(wrist_movement)
                            flag = 0
                if per == 0:
                    if dir == 1:
                        count += 0.5
                        dir = 0
                        if(flag==0):
                            wrist_movement = max(abs(wrist_coords[1] - prev2[1]), abs(wrist_coords[0] - prev2[0])) 
                            prev2[0]=wrist_coords[-2]
                            prev2[1]=wrist_coords[-1]
                            print(wrist_movement)
                            flag = 1
                
            cTime = time.time()
            if cTime - pTime > 60 or stop_flag():
                break

        results["reps"] = int(count)
        results["time_taken"] = int(cTime - pTime)
        cap.release()
        return results
                                     
