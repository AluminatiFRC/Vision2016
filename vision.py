import argparse
import cv2
import json
import math
import mqttClient
import numpy as np
import sys
import time
import paho.mqtt.client as mqtt

from WeightedFramerateCounter import WeightedFramerateCounter
from RealtimeInterval import RealtimeInterval
from CVParameterGroup import CVParameterGroup
import TriangleSimilarityDistanceCalculator as DistanceCalculator
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

MQTT_TOPIC_TARGETTING = "robot/vision/telemetry"
MQTT_TOPIC_SCREENSHOT = "robot/vision/screenshot"

cameraFrameWidth = None
cameraFrameHeight = None
testImage = None

#if debugMode:
#    testImage = cv2.imread("./screenshots/target003_simple.png")
#    cameraFrameHeight, cameraFrameWidth = testImage.shape[:2]

def takeScreenshot():
    filename = str(time.time()) + ".png"
    cv2.imwrite(filename, raw)
    return filename

def filterHue(source, hue, hueWidth, low, high):
    MAX_HUE = 179
    hsv = cv2.cvtColor(source, cv2.COLOR_BGR2HSV)

    lowHue = max(hue - hueWidth, 0)
    lowFilter = np.array([lowHue, low, low])

    highHue = min(hue + hueWidth, MAX_HUE)
    highFilter = np.array([highHue, high, high])
    
    return cv2.inRange(hsv, lowFilter, highFilter)

def messageHandler(message):
    #sys.stdout.write(".")
    #print message.topic
    #print message.payload
    if message.topic == MQTT_TOPIC_SCREENSHOT:
        filename = takeScreenshot()        

def createCamera():
    global cameraFrameWidth
    global cameraFrameHeight
    
    camera = cv2.VideoCapture(0)
    #No camera's exposure goes this low, but this will set it as low as possible
    #camera.set(cv2.cv.CV_CAP_PROP_EXPOSURE,-100)    
    #camera.set(cv2.cv.CV_CAP_PROP_FPS, 15)
    #camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
    #camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
    cameraFrameWidth = int(camera.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
    cameraFrameHeight = int(camera.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
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

# box is an array of two arrays each with two values (x and y)
def getIndexOfTopLeftCorner(box):
    ordered = sorted(box, key = distanceSqr)[:1][0]
    # got the point, but now get its index in the original list
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

def getTargetBoxTight(target):
    # Turn (array of array of array) into (array of array)
    target = target.reshape([-1,2])

    anchors = [\
        (0, 0),\
        (cameraFrameWidth, 0),\
        (cameraFrameWidth, cameraFrameHeight),\
        (0, cameraFrameHeight)]

    # Take the first point and use it as our best guess on all four corners
    candidates = [\
        {'p':target[0], 'd':distanceSqr(target[0], anchors[0])},\
        {'p':target[0], 'd':distanceSqr(target[0], anchors[1])},\
        {'p':target[0], 'd':distanceSqr(target[0], anchors[2])},\
        {'p':target[0], 'd':distanceSqr(target[0], anchors[3])}]

    for point in target:
        for i in range(4):
            distance = distanceSqr(anchors[i], point)
            if distance < candidates[i]['d']:
                candidates[i]['p'] = point
                candidates[i]['d'] = distance
    box = (tuple(candidates[0]['p']),\
           tuple(candidates[1]['p']),\
           tuple(candidates[2]['p']),\
           tuple(candidates[3]['p']))

    #print box
    #print getTargetBox(target)
    return box

def getTargetHeight(box):
    topLeftIndex = getIndexOfTopLeftCorner(box)
    centerLine = getboxCenterLine(box, topLeftIndex)
    boxHeight = math.sqrt(distanceSqr(centerLine[0], centerLine[1]))
    return boxHeight, centerLine

def main():
    connectThrottle = RealtimeInterval(10)
    host = "roboRIO-5495-FRC.local"
    port = 5888
    topics = (MQTT_TOPIC_SCREENSHOT)
    client = mqttClient.MqttClient(host, port, topics, messageHandler)

    params = CVParameterGroup("Sliders", debugMode)
    # HUES: GREEEN=65/75 BLUE=110
    params.addParameter("hue", 75, 179)
    params.addParameter("hueWidth", 20, 25)
    params.addParameter("low", 70, 255)
    params.addParameter("high", 255, 255)       
    params.addParameter("countourSize", 50, 200)
    params.addParameter("keystone", 0, 320)

    camera = cameraReader = None
    if testImage is None:
        camera = createCamera()
        cameraReader = CameraReaderAsync.CameraReaderAsync(camera)
    distanceCalculatorH = distanceCalculatorV  = None
    if tuneDistance:
        distanceCalculatorH = DistanceCalculator.TriangleSimilarityDistanceCalculator(TARGET_WIDTH)
        distanceCalculatorV = DistanceCalculator.TriangleSimilarityDistanceCalculator(TARGET_HEIGHT)
    else:
        distanceCalculatorH = DistanceCalculator.TriangleSimilarityDistanceCalculator(TARGET_WIDTH, DistanceCalculator.PFL_H_LC3000)
        distanceCalculatorV = DistanceCalculator.TriangleSimilarityDistanceCalculator(TARGET_HEIGHT, DistanceCalculator.PFL_V_LC3000)
    
    fpsDisplay = True
    fpsCounter = WeightedFramerateCounter()
    fpsInterval = RealtimeInterval(5.0, False)

    keyStoneBoxSource = [[0, 0], [cameraFrameWidth, 0], [cameraFrameWidth, cameraFrameHeight], [0, cameraFrameHeight]]

    # The first frame we take off of the camera won't have the proper exposure setting
    # We need to skip the first frame to make sure we don't process bad image data.
    frameSkipped = False

    while (True):
        if (not client.isConnected()) and connectThrottle.hasElapsed():
            try:
                client.connect()
            except:
                None

        # This code will load a test image from disk and process it instead of the camera input
        #raw = cv2.imread('test.png')
        #frameSkipped = True
        #if raw == None or len(raw) == 0:
        #    print "Can't load image"
        #    break
        if testImage is not None:
            raw = testImage.copy()
        elif cameraReader is not None:
            raw = cameraReader.Read()
        if raw != None and frameSkipped:
            fpsCounter.tick()
            
            if debugMode:
                if fpsDisplay:
                    cv2.putText(raw, "{:.0f} fps".format(fpsCounter.getFramerate()), (cameraFrameWidth - 100, 13 + 6), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,255,255), 1)
                cv2.imshow("raw", raw)

            # This will "deskew" or fix the keystone of a tilted camera.
            #ptSrc = np.float32([keyStoneBoxSource])
            #ptDst = np.float32([[params['keystone'], 0],\
            #                    [cameraFrameWidth - params['keystone'], 0],\
            #                    [cameraFrameWidth + params['keystone'], cameraFrameHeight],\
            #                    [-params['keystone'], cameraFrameHeight]])
            #matrix = cv2.getPerspectiveTransform(ptSrc, ptDst)
            #transformed = cv2.warpPerspective(raw, matrix, (cameraFrameWidth, cameraFrameHeight))
            #cv2.imshow("keystone", transformed)
            #target = findTarget(transformed, params)
            target = findTarget(raw, params)
            
            if target == None or not target.any():
                payload = { 'hasTarget': False, "fps": round(fpsCounter.getFramerate()) }
                client.publish(MQTT_TOPIC_TARGETTING, json.dumps(payload))
            else:
                distance = None

                targetBox = getTargetBoxTight(target)
                # We can tell how off-axis we are by looking at the slope
                # of the top off the targetBox. If we are on-center they will
                # be even. If we are off axis they will be unequal.
                # We are to the right of the target if the line slopes up to the right
                # and the slope is positive.
                offAxis = (targetBox[0][1] - targetBox[1][1]) / (cameraFrameHeight / 10.0)
                measuredHeight, centerLine = getTargetHeight(targetBox)
                center = (round((centerLine[0][0] + centerLine[1][0]) / 2),\
                          round((centerLine[0][1] + centerLine[1][1]) / 2))
                horizontalOffset = center[0] - (cameraFrameWidth / 2.0)
                
                perceivedFocalLengthH = perceivedFocalLengthV = 0.0
                if tuneDistance:
                    perceivedFocalLengthH = distanceCalculatorH.CalculatePerceivedFocalLengthAtGivenDistance(w, TARGET_CALIBRATION_DISTANCE)
                    perceivedFocalLengthV = distanceCalculatorV.CalculatePerceivedFocalLengthAtGivenDistance(h, TARGET_CALIBRATION_DISTANCE)
                    distance = TARGET_CALIBRATION_DISTANCE
                else:
                    # We use the height at the center of the taget to determine distance
                    # That way we hope it will be less sensitive to off-axis shooting angles
                    
                    distance = distanceCalculatorV.CalculateDistance(measuredHeight)
                distance = round(distance, 1)

                horizDelta = horizontalOffset / cameraFrameWidth * 2
                payload = {\
                    'horizDelta': horizDelta,\
                    'targetDistance': round(distance),\
                    'hasTarget': True,\
                    "fps": round(fpsCounter.getFramerate()),\
                    "offAxis": offAxis}
                client.publish(MQTT_TOPIC_TARGETTING, json.dumps(payload))

                if debugMode:
                    result = raw.copy()

                    # Draw the actual contours
                    #cv2.drawContours(result, target, -1, (255, 255, 255), 1)

                    # Draw the bounding area (targetBox)
                    cv2.drawContours(result, [np.int0(targetBox)], -1, (255, 0, 0), 1)

                    # Draw Convex Hull
                    #hull = cv2.convexHull(target)
                    #cv2.drawContours(result, hull, -1, (255, 0, 255), 1)
                    #temp = []
                    #for c in target:
                    #    contour = [c][0][0]
                    #    temp.append(contour)
                    #    #print contour
                    ##print temp
                    #top = getIndexOfTopLeftCorner(temp)
                    ##print target[top][0]
                    #cv2.circle(result, (target[top][0][0], target[top][0][1]), 3, (255, 255, 255), -1)

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
                        cv2.putText(result, "{:.0f} fps".format(fpsCounter.getFramerate()), (cameraFrameWidth - 100, 13 + 6), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,255,255), 1)
                    cv2.imshow("result", result)

        if raw != None:
            frameSkipped = True
        if fpsDisplay and fpsInterval.hasElapsed():
            print "{0:.1f} fps (processing)".format(fpsCounter.getFramerate())
            if cameraReader is not None:
                print "{0:.1f} fps (camera)".format(cameraReader.fps.getFramerate())
    
        if debugMode:
            keyPress = cv2.waitKey(1)
            if keyPress != -1:
                keyPress = keyPress & 0xFF
            if keyPress == ord("f"):
                fpsDisplay = not fpsDisplay
            elif keyPress == ord("q"):
                break 
            elif keyPress == ord("z"):
                takeScreenshot()

    client.disconnect()
    if cameraReader is not None:
        cameraReader.Stop()
    if camera is not None:
        camera.release()
    cv2.destroyAllWindows()

parser = argparse.ArgumentParser(description="Vision-based targetting system for FRC 2016")
parser.add_argument("--release", dest="releaseMode", action="store_const", const=True, default=not debugMode, help="hides all debug windows (default: False)")
args = parser.parse_args()
debugMode = not args.releaseMode

main()
