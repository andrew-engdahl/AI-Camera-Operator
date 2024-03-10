import cv2
import mediapipe as mp
import time
import numpy as np
import os
import math
import statistics
import mido

# Create a MIDI Ouput

midiPort = mido.open_output(mido.get_output_names()[1])

# from mido.sockets import PortServer, connect
# for message in PortServer('localhost', 5004):
#     print(message)
# session = connect('localhost', 5004)

# Mediapipe Config
# BaseOptions = mp.tasks.BaseOptions
# PoseLandmarker = mp.tasks.vision.PoseLandmarker
# PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
# VisionRunningMode = mp.tasks.vision.RunningMode

# options = PoseLandmarkerOptions(
#     running_mode=VisionRunningMode.LIVE_STREAM,
#     min_tracking_confidence=0.8)

torsoPoints = {'x': [], 'y': []}

txt = ""

# Colors
blue = (255,0,0)
green = (0,255,0)
red = (0,0,255)
magenta = (255,0,255)
white = (255,255,255)

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose
pose = mpPose.Pose()

# Set Capture Size
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Set Options
xDeadZone = .05
yDeadZone = .33
smoothing = 20

while True:
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = pose.process(imgRGB)

    height, width = img.shape[:2]

    leftBound = int(width * (0.5 - xDeadZone))
    rightBound = int(width * (0.5 + xDeadZone))
    topBound = int(height * (0.5 - yDeadZone))
    bottomBound = int(height * (0.5 - yDeadZone))

    if results.pose_landmarks:
        mpDraw.draw_landmarks(img,results.pose_landmarks, mpPose.POSE_CONNECTIONS)
        for id, lm in enumerate(results.pose_landmarks.landmark):

            if id == 11 or id == 12 or id == 23 or id == 24: # Torso

                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                x, y = float("{:.2f}".format(lm.x)), float("{:.2f}".format(lm.y))
                cv2.circle(img, (cx, cy), 5, red, cv2.FILLED)

                if len(torsoPoints['x']) > smoothing:
                    del torsoPoints['x'][0]
                    del torsoPoints['y'][0]

                torsoPoints['x'].append(x)
                torsoPoints['y'].append(y)

        # Get Body Alignment
        #print(torsoPoints)
        s1x = statistics.mean([results.pose_landmarks.landmark[23].x, results.pose_landmarks.landmark[24].x])
        s1y = statistics.mean([results.pose_landmarks.landmark[23].y, results.pose_landmarks.landmark[24].y])
        s2x = statistics.mean([results.pose_landmarks.landmark[11].x, results.pose_landmarks.landmark[12].x])
        s2y = statistics.mean([results.pose_landmarks.landmark[11].y, results.pose_landmarks.landmark[12].y])

        # Get Torso Center
        torsoCenter = (int(statistics.mean(torsoPoints['x']) * width), int((statistics.mean(torsoPoints['y'])) * height))
        cv2.circle(img, torsoCenter, 5, green, cv2.FILLED)

        # # Get Slope of body
        # if (s2x - s1x) != 0:
        #     m = (s2y - s1y) / (s2x - s1x)
        # else: # Temp workaround for 0 diff in Xs
        #     m = (s2y - s1y) / 0.00000001

        # # Get Y-Intercept
        # b = s1y - m * s1x

        # # Set Torso to Head Ratio and Calculate
        # f = 2/3
        # torsoLength = math.sqrt(math.pow(abs(s2x-s1x),2)+math.pow(abs(s2y-s1y),2))
        # sx = s2x + (m/abs(m))*(torsoLength*f*math.cos(math.atan(m)))
        # sy = m*sx+b
        # headPosition = (int(sx * width), int((1-sy) * height))

        # print(headPosition)
        # cv2.circle(img, headPosition, 5, magenta, cv2.FILLED)

        if torsoCenter[0] > leftBound and torsoCenter[0] < rightBound:
            txt = ""
            midiPort.send(mido.Message('note_off', channel=0, note=60))
            midiPort.send(mido.Message('note_off', channel=0, note=61))
        elif torsoCenter[0] <= leftBound:
            panStrength = (leftBound - torsoCenter[0]) / leftBound
            txt = "pan-left" + str(panStrength)
            # Send a MIDI message
            midiPort.send(mido.Message('note_off', channel=0, note=61))
            midiPort.send(mido.Message('note_on', channel=0, note=60, velocity=127))
        elif torsoCenter[0] >= rightBound:
            panStrength = (torsoCenter[0] - rightBound) / leftBound
            midiPort.send(mido.Message('note_off', channel=0, note=60))
            midiPort.send(mido.Message('note_on', channel=0, note=61, velocity=127))
            txt = "pan-right" + str(panStrength)
                
    cv2.putText(img, txt, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, white, 1)

    # Draw bounding lines
    cv2.line(img, (leftBound,0), (leftBound,height), magenta, 1)
    cv2.line(img, (rightBound,0), (rightBound,height), magenta, 1)
    cv2.line(img, (0,topBound), (width, topBound), magenta, 1)
    cv2.line(img, (0,bottomBound), (width, bottomBound), magenta, 1)

    cv2.imshow("Visual Results", img)
    cv2.waitKey(1)

# Close the session
midiPort.close()
