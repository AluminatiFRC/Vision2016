import sys
import math
import paho.mqtt.client as mqtt
from WeightedFramerateCounter import WeightedFramerateCounter
from RealtimeInterval import RealtimeInterval
from CVParameterGroup import CVParameterGroup
import TriangleSimilarityDistanceCalculator as DistanceCalculator
import numpy as np
import cv2
import time
import mqttClient
import json
import CameraReaderAsync

debugMode = True

tuneDistance = False and debugMode

BLUECASE_WIDTH = 14
BLUECASE_HEIGHT = 10.5
TESTTAPE_WIDTH = 11.25
RETROREFLECTIVE_TAPE_SIZE = 2
COMPETITION_TARGET_WIDTH = 20
COMPETITION_TARGET_HEIGHT = 14

TARGET_CALIBRATION_DISTANCE = 67
TARGET_WIDTH = COMPETITION_TARGET_WIDTH
TARGET_HEIGHT = COMPETITION_TARGET_HEIGHT

def filterHue(source, hue, hueWidth, low, high):
    MAX_HUE = 179
    hsv = cv2.cvtColor(source, cv2.COLOR_BGR2HSV)

    lowHue = max(hue - hueWidth, 0)
    lowFilter = np.array([lowHue, low, low])

    highHue = min(hue + hueWidth, MAX_HUE)
    highFilter = np.array([highHue, high, high])
    
    return cv2.inRange(hsv, lowFilter, highFilter)

def messageHandler(message):
    sys.stdout.write(".")
    #print message.topic
    #print message.payload

def createCamera():
    camera = cv2.VideoCapture(0)
    #No camera's exposure goes this low, but this will set it as low as possible
    camera.set(cv2.cv.CV_CAP_PROP_EXPOSURE,-100)    
    #camera.set(cv2.cv.CV_CAP_PROP_FPS, 15)
    #camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
    #camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
    return camera

##
## This takes a raw BGR image and determines if it contains the target we are looking for.
##
def findTarget(raw, params): 
    mask = filterHue(raw, params["hue"], params["hueWidth"], params["low"], params["high"])
    #cv2.imshow("mask", mask)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) > 0:
        ordered = sorted(contours, key = cv2.contourArea, reverse = True)[:1]
        largestContour = ordered[0]
        if largestContour != None and cv2.contourArea(largestContour) > params["countourSize"]:
            return largestContour

def distanceSqr(p1, p2 = (0,0)):
    return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2

# box is array is array for two values  (x and y)
def getIndexOfTopLeftCorner(box):
    ordered = sorted(box, key = distanceSqr)[:1][0]
    # got the point, but what is its index in the original list?
    for i in range(len(box)):
        if box[i][0] == ordered[0] and box[i][1] == ordered[1]:
            return i

def getboxCenterLine(box, index):
    topX = box[(index + 0) % 4][0] + ((box[(index + 1) % 4][0] - box[(index + 0) % 4][0]) / 2)
    topY = box[(index + 0) % 4][1] + ((box[(index + 1) % 4][1] - box[(index + 0) % 4][1]) / 2)
    botX = box[(index + 3) % 4][0] + ((box[(index + 2) % 4][0] - box[(index + 3) % 4][0]) / 2)
    botY = box[(index + 3) % 4][1] + ((box[(index + 2) % 4][1] - box[(index + 3) % 4][1]) / 2)
    return ((topX, topY), (botX, botY))

def getTargetBox(target):
    minRect = cv2.minAreaRect(target)
    box = cv2.cv.BoxPoints(minRect)
    #box = np.int0(box) # convert points to ints
    return box

def getTargetHeight(box):
    topLeftIndex = getIndexOfTopLeftCorner(box)
    centerLine = getboxCenterLine(box, topLeftIndex)
    boxHeight = math.sqrt(distanceSqr(centerLine[0], centerLine[1]))
    return boxHeight, centerLine

def main():
    connectThrottle = RealtimeInterval(10)
    MQTT_TOPIC_TARGETTING = "5495.targetting"
    host = "roboRIO-5495-FRC.local"
    port = 5888
    topics = ()
    client = mqttClient.MqttClient(host, port, topics, messageHandler)

    params = CVParameterGroup("Sliders", debugMode)
    # HUES: GREEEN=65/75 BLUE=110
    params.addParameter("hue", 75, 179)
    params.addParameter("hueWidth", 5, 25)
    params.addParameter("low", 70, 255)
    params.addParameter("high", 255, 255)       
    params.addParameter("countourSize", 50, 200)

    camera = createCamera()
    cameraReader = CameraReaderAsync.CameraReaderAsync(camera)
    distanceCalculatorH = distanceCalculatorV  = None
    if tuneDistance:
        distanceCalculatorH = DistanceCalculator.TriangleSimilarityDistanceCalculator(TARGET_WIDTH)
        distanceCalculatorV = DistanceCalculator.TriangleSimilarityDistanceCalculator(TARGET_HEIGHT)
    else:
        distanceCalculatorH = DistanceCalculator.TriangleSimilarityDistanceCalculator(TARGET_WIDTH, DistanceCalculator.PFL_H_LC3000)
        distanceCalculatorV = DistanceCalculator.TriangleSimilarityDistanceCalculator(TARGET_HEIGHT, DistanceCalculator.PFL_V_LC3000)
    
    fpsDisplay = False;
    fpsCounter = WeightedFramerateCounter()
    fpsInterval = RealtimeInterval(5.0)

    # The first frame we take off of the camera won't have the proper exposure setting
    # We need to skip the first frame to make sure we don't process bad image data.
    frameSkipped = False;

    raw = cv2.imread('test.png')
    cv2.imshow("raw", raw);

    while (True):
        if (not client.isConnected()) and connectThrottle.hasElapsed():
            try:
                None#client.connect()
            except:
                None
        
        #raw = cameraReader.Read()
        if raw != None and frameSkipped:
            fpsCounter.tick()
            
            if debugMode:
                if fpsDisplay:
                    cv2.putText(raw, "{:.0f} fps".format(fpsCounter.getFramerate()), (640 - 100, 13 + 6), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,255,255), 1)
                cv2.imshow("raw", raw);

            target = findTarget(raw, params)
            if target == None or not target.any():
                payload = { 'hasTarget': False, "fps": round(fpsCounter.getFramerate()) }
                client.publish(MQTT_TOPIC_TARGETTING, json.dumps(payload))
            else:
                distance = None

                targetBox = getTargetBox(target)
                measuredHeight, centerLine = getTargetHeight(targetBox)
                center = (round((centerLine[0][0] + centerLine[1][0]) / 2),\
                          round((centerLine[0][1] + centerLine[1][1]) / 2))
                horizontalOffset = center[0] - 320
                
                perceivedFocalLengthH = perceivedFocalLengthV = 0.0
                if tuneDistance:
                    perceivedFocalLengthH = distanceCalculatorH.CalculatePerceivedFocalLengthAtGivenDistance(w, TARGET_CALIBRATION_DISTANCE);
                    perceivedFocalLengthV = distanceCalculatorV.CalculatePerceivedFocalLengthAtGivenDistance(h, TARGET_CALIBRATION_DISTANCE);
                    distance = TARGET_CALIBRATION_DISTANCE
                else:
                    # We use the height at the center of the taget to determine distance
                    # That way we hope it will be less sensitive to off-axis shooting angles
                    
                    distance = distanceCalculatorV.CalculateDistance(measuredHeight);
                distance = round(distance, 1)

                payload = { 'horizDelta': horizontalOffset, 'targetDistance': round(distance), 'hasTarget': True, "fps": round(fpsCounter.getFramerate()) }
                client.publish(MQTT_TOPIC_TARGETTING, json.dumps(payload))

                if debugMode:
                    result = raw.copy()

                    # Draw the centerline that represent the height
                    cv2.line(result, (int(round(centerLine[0][0])), int(round(centerLine[0][1]))),\
                                     (int(round(centerLine[1][0])), int(round(centerLine[1][1]))),\
                                     (128, 0, 255), 1)
                    
                    # draw the center of the object
                    cv2.circle(result, (int(round(center[0])), int(round(center[1]))), 4, (250, 250, 250), -1)
                    
                    #cv2.putText(result, str(horizontalOffset), (x-50, y+15), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 0, 0), 1)
                    if tuneDistance:
                        cv2.putText(result, "PFL_H: {:.0f}".format(perceivedFocalLengthH), (3, 13 + 5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,255,255), 1)
                        cv2.putText(result, "PFL_V: {:.0f}".format(perceivedFocalLengthV), (3, 13 + 5 + 22), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,255,255), 1)
                    else:
                        cv2.putText(result, "{} inches".format(distance), (3, 13 + 5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,255,255), 1)
                    if fpsDisplay:
                        cv2.putText(result, "{:.0f} fps".format(fpsCounter.getFramerate()), (640 - 100, 13 + 6), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,255,255), 1)
                    cv2.imshow("result", result)
                    raw = None
        if raw != None:
           frameSkipped = True 
        if fpsDisplay and fpsInterval.hasElapsed():
            print "{0:.1f} fps".format(fpsCounter.getFramerate())
        
        keyPress = cv2.waitKey(1)
        if keyPress == ord("f"):
            fpsDisplay = not fpsDisplay
        elif keyPress == ord("q"):
            break 
        elif keyPress == ord("z"):
            filename = str(time.time()) + ".png"
            cv2.imwrite(filename, raw)
            print "Took screenshot " + filename

    client.disconnect()
    cameraReader.Stop()
    camera.release()
    cv2.destroyAllWindows()

main()
