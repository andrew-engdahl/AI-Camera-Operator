import cv2
import mediapipe as mp
import time
import numpy as np
import os
import math
import statistics
import mido

noMidi = True
midiChannel = 2

# Create a MIDI Ouput
try:
    midiPort = mido.open_output(mido.get_output_names()[1])
    noMidi = False
    print(mido.get_output_names())
    print("MIDI Connected: " + mido.get_output_names()[1])
except:
    print("No MIDI outputs detected")

#headPoints = {'x': [], 'y': []}
shoulderPoints = {'x': [], 'y': []}
torsoPoints = {'x': [], 'y': []}
hipPoints = {'x': [], 'y': []}

txt = ""
txt2 = ""
txt3 = ""

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
yDeadZone = .2
smoothing = 20
yTolerance = 0.05

while True:
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = pose.process(imgRGB)

    height, width = img.shape[:2]

    leftBound = int(width * (0.5 - xDeadZone))
    rightBound = int(width * (0.5 + xDeadZone))
    topBound = int(height * (0.5 - yDeadZone))
    bottomBound = int(height * (0.5 + yDeadZone))

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
        s1x = int(statistics.mean([results.pose_landmarks.landmark[23].x, results.pose_landmarks.landmark[24].x]) * width)
        s1y = int(statistics.mean([results.pose_landmarks.landmark[23].y, results.pose_landmarks.landmark[24].y]) * height)
        s2x = int(statistics.mean([results.pose_landmarks.landmark[11].x, results.pose_landmarks.landmark[12].x]) * width)
        s2y = int(statistics.mean([results.pose_landmarks.landmark[11].y, results.pose_landmarks.landmark[12].y]) * height)

        s1 = s1x, s1y
        s2 = s2x, s2y

        cv2.circle(img, s1, 5, magenta, cv2.FILLED)
        cv2.circle(img, s2, 5, magenta, cv2.FILLED)

        # Sholder Points
        if len(shoulderPoints['x']) > smoothing:
            del shoulderPoints['x'][0]
            del shoulderPoints['y'][0]

        shoulderPoints['x'].append(s2x)
        shoulderPoints['y'].append(s2y)

        # Hip Points
        if len(hipPoints['x']) > smoothing:
            del hipPoints['x'][0]
            del hipPoints['y'][0]

        hipPoints['x'].append(s1x)
        hipPoints['y'].append(s1y)

        # Calculate and draw smoothed Data Points
        shoulderCenter = int(statistics.mean(shoulderPoints['x'])), int(statistics.mean(shoulderPoints['y']))
        torsoCenter = (int(statistics.mean(torsoPoints['x']) * width), int((statistics.mean(torsoPoints['y'])) * height))
        hipCenter = int(statistics.mean(hipPoints['x'])), int(statistics.mean(hipPoints['y']))
        
        cv2.circle(img, shoulderCenter, 5, white, cv2.FILLED)
        cv2.circle(img, torsoCenter, 5, white, cv2.FILLED)
        cv2.circle(img, hipCenter, 5, white, cv2.FILLED)

        # # Get Slope of body
        # if (s2x - s1x) != 0:
        #     m = (s2y - s1y) / (s2x - s1x)
        # else: # Temp workaround for 0 diff in Xs
        #     m = (s2y - s1y) / 0.00000001

        # # Get Y-Intercept
        # b = s1y - m * s1x

        # # Set Torso to Head Ratio and Calculate
        # f = 0.6
        # torsoLength = math.sqrt(math.pow(abs(s2x-s1x),2)+math.pow(abs(s2y-s1y),2))
        # sx = s2x + (torsoLength*f*math.cos(math.atan(m)))*(-m/abs(m))
        # sy = m*sx+b

        # if len(headPoints['x']) > int(smoothing / 4):
        #     del headPoints['x'][0]
        #     del headPoints['y'][0]

        # headPoints['x'].append(sx)
        # headPoints['y'].append(sy)
        # headCenter = int(statistics.mean(headPoints['x'])), int(statistics.mean(headPoints['y']))

        # # Display Calculated Head Point
        # cv2.circle(img, headCenter, 5, green, cv2.FILLED)

        # Pan Controls
        if torsoCenter[0] > leftBound and torsoCenter[0] < rightBound:
            txt = ""
            if not noMidi:
                midiPort.send(mido.Message('note_off', channel=midiChannel, note=60))
                midiPort.send(mido.Message('note_off', channel=midiChannel, note=61))
                txt = "No Pan:"
        elif torsoCenter[0] <= leftBound:
            panStrength = (leftBound - torsoCenter[0]) / leftBound
            txt = "pan-left : " + str(panStrength)
            # Send a MIDI message
            if not noMidi:
                midiPort.send(mido.Message('note_off', channel=midiChannel, note=61))
                midiPort.send(mido.Message('note_on', channel=midiChannel, time=100, note=60, velocity=int(127 * panStrength)))
        elif torsoCenter[0] >= rightBound:
            panStrength = (torsoCenter[0] - rightBound) / leftBound
            if not noMidi:
                midiPort.send(mido.Message('note_off', channel=midiChannel, note=60))
                midiPort.send(mido.Message('note_on', channel=midiChannel, time=100, note=61, velocity=int(127 * panStrength)))
            txt = "pan-right : " + str(panStrength)

        # Tilt Controls
        if shoulderCenter[1] > topBound and shoulderCenter[1] < topBound + (height * yTolerance):
            txt2 = ""
            if not noMidi:
                midiPort.send(mido.Message('note_off', channel=midiChannel, note=50))
                midiPort.send(mido.Message('note_off', channel=midiChannel, note=51))
                txt2 = "No Tilt:"
        elif shoulderCenter[1] <= topBound:
            #panStrength = (leftBound - torsoCenter[0]) / leftBound
            tiltStrength = 1
            txt2 = "tilt-up : " + str(tiltStrength)
            if not noMidi:
                midiPort.send(mido.Message('note_off', channel=midiChannel, note=51))
                midiPort.send(mido.Message('note_on', channel=midiChannel, time=100, note=50, velocity=int(127 * tiltStrength)))
        elif shoulderCenter[1] >= topBound + (height * yTolerance):
            #panStrength = (torsoCenter[0] - rightBound) / leftBound
            tiltStrength = 1
            if not noMidi:
                midiPort.send(mido.Message('note_off', channel=midiChannel, note=50))
                midiPort.send(mido.Message('note_on', channel=midiChannel, time=100, note=51, velocity=int(127 * tiltStrength)))
            txt2 = "tilt-down : " + str(tiltStrength)

        # Zoom Controls
        torsoHeight = abs(shoulderCenter[1] - hipCenter[1])
        if torsoHeight < abs(topBound - bottomBound): # Zoom In
            if not noMidi:
                midiPort.send(mido.Message('note_off', channel=midiChannel, note=71))
                midiPort.send(mido.Message('note_on', channel=midiChannel, time=100, note=70, velocity=127))
                txt3 = "Zoom In:"
        elif torsoHeight > abs((topBound + (height * yTolerance)) - bottomBound): # Zoom Out
            if not noMidi:
                midiPort.send(mido.Message('note_off', channel=midiChannel, note=70))
                midiPort.send(mido.Message('note_on', channel=midiChannel, time=100, note=71, velocity=127))
                txt3 = "Zoom Out:"
        elif torsoHeight >= abs(topBound - bottomBound) and torsoHeight <= abs((topBound + (height * yTolerance)) - bottomBound): 
            txt3 = ""
            if not noMidi:
                midiPort.send(mido.Message('note_off', channel=midiChannel, note=50))
                midiPort.send(mido.Message('note_off', channel=midiChannel, note=51))
                txt3 = "No Zoom:"
                
    cv2.putText(img, txt, (20,40), cv2.FONT_HERSHEY_SIMPLEX, 1, white, 1)
    cv2.putText(img, txt2, (20,80), cv2.FONT_HERSHEY_SIMPLEX, 1, white, 1)
    cv2.putText(img, txt3, (20,120), cv2.FONT_HERSHEY_SIMPLEX, 1, white, 1)

    # Draw bounding lines
    cv2.line(img, (leftBound,0), (leftBound,height), magenta, 1)
    cv2.line(img, (rightBound,0), (rightBound,height), magenta, 1)
    cv2.line(img, (0,topBound), (width, topBound), magenta, 1)
    topTol = topBound + int(height * yTolerance)
    cv2.line(img, (0, topTol), (width, topTol), magenta, 1)
    cv2.line(img, (0,bottomBound), (width, bottomBound), magenta, 1)

    cv2.imshow("Visual Results", img)
    cv2.waitKey(1)

# Close the session
midiPort.close()
