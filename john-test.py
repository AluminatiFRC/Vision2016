import sys
import paho.mqtt.client as mqtt
from WeightedFramerateCounter import WeightedFramerateCounter
from RealtimeInterval import RealtimeInterval
from CVParameterGroup import CVParameterGroup
from TriangleSimilarityDistanceCalculator import TriangleSimilarityDistanceCalculator 
import numpy as np
import cv2
import time
import mqttClient
import json

debugMode = False

def filterHue(source):
    MAX_HUE = 179
    hsv = cv2.cvtColor(source, cv2.COLOR_BGR2HSV)
    x = params["hue"] - params["hueWidth"]
    if x < 0:
         x = MAX_HUE - (MAX_HUE % x)
    low = np.array([x, params["low"], params["low"]])

    x = params["hue"] + params["hueWidth"]
    if x > MAX_HUE:
         x = MAX_HUE % x
    high = np.array([x, params["high"], params["high"]])

    mask = cv2.inRange(hsv, low, high)
    return mask

def findLargestContour(source):
    contours, hierarchy = cv2.findContours(source, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) > 0:
        ordered = sorted(contours, key = cv2.contourArea, reverse = True)[:1]
        return ordered[0]

def messageHandler(message):
    sys.stdout.write(".")
    #print message.topic
    #print message.payload\

def createCamera():
    camera = cv2.VideoCapture(0)
    #No camera's exposure goes this low, but this will set it as low as possible
    camera.set(cv2.cv.CV_CAP_PROP_EXPOSURE,-100)
    #camera.set(cv2.cv.CV_CAP_PROP_FPS, 15)
    #camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
    #camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
    return camera

def processRawImage(raw): 
    cv2.imshow("raw", raw)
    
    mask = filterHue(raw)
    #cv2.imshow("mask", mask)

    #colorOnly = cv2.bitwise_and(raw, raw, mask = mask)
    #cv2.imshow("colormasked", colorOnly)
    #mask = cv2.threshold(mask, params["gray"], 255, 0)

    result = raw.copy()
    largestContour = findLargestContour(mask)
    if largestContour is not None:
##            M = cv2.moments(largestContour)
##            if M["m00"] != 0:
##                cx = int(M["m10"]/M["m00"])
##                cy = int(M["m01"]/M["m00"])
##                cv2.circle(result, (cx, cy), 8, (250, 250, 250), -1)
##                hull = cv2.convexHull(largestContour)
##                cv2.drawContours(result, [hull], 0, (0,255,0), 3)
        x,y,w,h = cv2.boundingRect(largestContour)
        center = (x+(w/2), y+(h/2))
        cv2.rectangle(result, (x,y), (x+w,y+h), (40,0,120), 2)
        cv2.circle(result, center, 8, (250, 250, 250), -1)
        cv2.putText(result, str(center[0]-320), (x-50, y+15), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,0,0), 1)
        cv2.putText(result, str(center[1]-240), (x-50, y+45), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,0,0), 1)

        #perceivedFocalLength = distanceCalc.CalculatePerceivedFOVAtGivenDistance(w, targetSize[1]);
        #params["FOV"] = int(perceivedFocalLength)
        perceivedFocalLength = 652  
        calc = TriangleSimilarityDistanceCalculator(targetSize[0], perceivedFocalLength)
        distance = calc.CalcualteDistance(w);
        cv2.putText(result, str(distance) + " inches", (5, 23), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,0,0), 1)

##            tPx = w
##            distance = params["FOV"]/w
##            cv2.putText(result, str(distance), (30, 30), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0,0,0), 1)
        #client.publish("5495.targetting", center[0]-320)

        payload = { 'horizDelta': center[0] - 320, 'targetDistance': int(distance) }
        client.publish(MQTT_TOPIC_TARGETTING, json.dumps(payload))
        return result

MQTT_TOPIC_TARGETTING = "5495.targetting"
host = "roboRIO-5495-FRC.local"
port = 5888
topics = ()
client = mqttClient.MqttClient(host, port, topics, messageHandler)

params = CVParameterGroup("Sliders")
if debugMode:
    params.showWindow()
params.addParameter("hue", 65, 255) # GREEN
#params.addParameter("hue", 105, 255) #BLUE
params.addParameter("hueWidth", 5, 25)
params.addParameter("FOV", 652, 50000)
params.addParameter("low", 70, 255)
params.addParameter("high", 255, 255)

camera = createCamera()

targetSize = (11.25, 44) # size, distance
distanceCalc = TriangleSimilarityDistanceCalculator(targetSize[0])

fpsDisplay = False;
fpsCounter = WeightedFramerateCounter()
fpsInterval = RealtimeInterval(3.0)

while (True):
    if not client.isConnected() :
        try:
            client.connect()
        except:
            None
    
    ret, raw = camera.read()
    
    if ret:
        fpsCounter.tick()
        result = processRawImage(raw)
        #cv2.imshow("result", result)
    
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
