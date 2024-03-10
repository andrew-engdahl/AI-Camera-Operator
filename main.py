import cv2
import mediapipe as mp
import time
import numpy as np
import os
import math

# Mediapipe Config
# BaseOptions = mp.tasks.BaseOptions
# PoseLandmarker = mp.tasks.vision.PoseLandmarker
# PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
# VisionRunningMode = mp.tasks.vision.RunningMode

# options = PoseLandmarkerOptions(
#     running_mode=VisionRunningMode.LIVE_STREAM,
#     min_tracking_confidence=0.8)

torsoPoints = {'x':{}, 'y': {}}

leftMostPoint = .5
rightMostPoint = .5

# Colors
blue = (255,0,0)
green = (0,255,0)
red = (0,0,255)
magenta = (255,0,255)
white = (255,255,255)

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose
pose = mpPose.Pose()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

pTime = 0

while True:
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = pose.process(imgRGB)

    height, width = img.shape[:2]
    leftBoundPercent = 0.2
    rightBoundPercent = 0.8
    topBoundPercent = 0.2
    bottomBoundPercent = 0.8
    leftBound = int(width * leftBoundPercent)
    rightBound = int(width * rightBoundPercent)
    topBound = int(height * topBoundPercent)
    bottomBound = int(height * bottomBoundPercent)

    str = ''

    if results.pose_landmarks:
        mpDraw.draw_landmarks(img,results.pose_landmarks, mpPose.POSE_CONNECTIONS)
        for id, lm in enumerate(results.pose_landmarks.landmark):

            if id == 11 or id == 12 or id == 23 or id == 24: # Torso

                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                x, y = float("{:.2f}".format(lm.x)), float("{:.2f}".format(lm.y))

                torsoPoints['x'][id] = x
                torsoPoints['y'][id] = y
                cv2.circle(img, (cx, cy), 5, red, cv2.FILLED)

        print(torsoPoints)
        try:
            leftMostPoint = min(torsoPoints['x'].values())
            rightMostPoint = max(torsoPoints['x'].values())
        except:
            print("torsoPoints not defined")

        if leftMostPoint <= leftBoundPercent and rightMostPoint >= rightBoundPercent:
            str = "zoom-out"
        else:
            if leftMostPoint <= leftBoundPercent:
                str = "pan-left"
            if rightMostPoint >= rightBoundPercent:
                str = "pan-right"

    # Get Body Alignment
    s1x = (torsoPoints['x'][23] + torsoPoints['x'][24]) / 2
    s1y = (torsoPoints['y'][23] + torsoPoints['y'][24]) / 2
    s2x = (torsoPoints['x'][11] + torsoPoints['x'][12]) / 2
    s2y = (torsoPoints['y'][11] + torsoPoints['y'][12]) / 2

    # Get Slope of body
    m = (s2y - s1y) / (s2x - s1x)

    # Get Y-Intercept
    b = s1y - m * s1x

    # Set Torso to Head Ratio and Calculate
    f = 3/4
    torsoLength = math.sqrt(math.pow(abs(s2x-s1x),2)+math.pow(abs(s2y-s1y),2))
    sx = s2x + (m/abs(m))(torsoLength*f*math.cos(math.atan(m)))
    sy = m(sx)+b


    cv2.circle(img, (sx, sy), 5, red, cv2.FILLED)

                
    cv2.putText(img, str, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, white, 1)

    # Draw bounding lines
    cv2.line(img, (leftBound,0), (leftBound,height), magenta, 1)
    cv2.line(img, (rightBound,0), (rightBound,height), magenta, 1)
    cv2.line(img, (0,topBound), (width, topBound), magenta, 1)
    cv2.line(img, (0,bottomBound), (width, bottomBound), magenta, 1)

    cv2.imshow("Visual Results", img)
    cv2.waitKey(1)