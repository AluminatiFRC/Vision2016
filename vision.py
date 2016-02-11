import sys
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

debugMode = True

tuneDistance = False and debugMode

BLUECASE_WIDTH = 14
BLUECASE_HEIGHT = 10.5
TESTTAPE_WIDTH = 11.25
TESTTAPE_HEIGHT = 2
TARGET_WIDTH = TESTTAPE_WIDTH
TARGET_HEIGHT = TESTTAPE_HEIGHT
TARGET_CALIBRATION_DISTANCE = 67

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
## This should take a raw BGR image and determine if it contains the target we are looking for
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

def main():
    MQTT_TOPIC_TARGETTING = "5495.targetting"
    host = "roboRIO-5495-FRC.local"
    port = 5888
    topics = ()
    client = mqttClient.MqttClient(host, port, topics, messageHandler)

    params = CVParameterGroup("Sliders", debugMode)
    # HUES: GREEEN=65/75 BLUE=110
    params.addParameter("hue", 65, 179)
    params.addParameter("hueWidth", 5, 25)
    params.addParameter("low", 70, 255)
    params.addParameter("high", 255, 255)
    params.addParameter("countourSize", 50, 200)

    camera = createCamera()
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

    while (True):
        if not client.isConnected() :
            try:
                None#client.connect()
            except:
                None
        
        ret, raw = camera.read()
        if ret:
            fpsCounter.tick()

            if debugMode:
                cv2.imshow("raw", raw);

            contour = findTarget(raw, params)
            if target == None or not target.any():
                payload = { 'hasTarget': False, "fps": fpsCounter.getFramerate() }
                client.publish(MQTT_TOPIC_TARGETTING, json.dumps(payload))
            else:
                x,y,w,h = cv2.boundingRect(target)
                center = (x + (w / 2), y + (h / 2))
                horizontalOffset = center[0] - 320

                distance = None
                perceivedFocalLengthH = perceivedFocalLengthV = 0.0
                if tuneDistance:
                    perceivedFocalLengthH = distanceCalculatorH.CalculatePerceivedFocalLengthAtGivenDistance(w, TARGET_CALIBRATION_DISTANCE);
                    perceivedFocalLengthV = distanceCalculatorV.CalculatePerceivedFocalLengthAtGivenDistance(h, TARGET_CALIBRATION_DISTANCE);
                    distance = TARGET_CALIBRATION_DISTANCE
                else:
                    # Use the largest axis to determine the physical distance
                    if w > h:
                        distance = distanceCalculatorH.CalcualteDistance(w);
                    else:
                        distance = distanceCalculatorV.CalcualteDistance(h);
                distance = round(distance, 1)

                payload = { 'horizDelta': horizontalOffset, 'targetDistance': int(distance), 'hasTarget': True, "fps": fpsCounter.getFramerate() }
                client.publish(MQTT_TOPIC_TARGETTING, json.dumps(payload))

                if debugMode:
                    result = raw.copy()
                    cv2.rectangle(result, (x, y), (x + w, y + h), (40, 0, 120), 2)
                    cv2.circle(result, center, 8, (250, 250, 250), -1)
                    cv2.putText(result, str(horizontalOffset), (x-50, y+15), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 0, 0), 1)
                    if tuneDistance:
                        cv2.putText(result, "PFL_H: {:.0f}".format(perceivedFocalLengthH), (3, 13 + 5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,255,255), 1)
                        cv2.putText(result, "PFL_V: {:.0f}".format(perceivedFocalLengthV), (3, 13 + 5 + 22), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,255,255), 1)
                    else:
                        cv2.putText(result, "{} inches".format(distance), (3, 13 + 5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,255,255), 1)
                    if fpsDisplay:
                        cv2.putText(result, "{:.0f} fps".format(fpsCounter.getFramerate()), (640 - 100, 13 + 6), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,255,255), 1)
                    cv2.imshow("result", result)

        if fpsDisplay and fpsInterval.hasElapsed():
            print "{0:.1f} fps".format(fpsCounter.getFramerate())
        
        keyPress = cv2.waitKey(1)
        if keyPress == ord("f"):
            fpsDisplay = not fpsDisplay
        elif keyPress == ord("q"):
            break 
        elif keyPress == ord("z"):
            cv2.imwrite(str(time.time()) + ".png", raw)
            print "Took screenshot"

    camera.release()
    cv2.destroyAllWindows()

main()
