from WeightedFramerateCounter import WeightedFramerateCounter
from RealtimeInterval import RealtimeInterval
from CVParameterGroup import CVParameterGroup
import numpy as np
import cv2
import time

def filterHue(source):
    hsv = cv2.cvtColor(source, cv2.COLOR_BGR2HSV)
    x = params["hue"] - params["hueWidth"]
    if x < 0:
         x = 0
    low = np.array([x, params["low"], params["low"]])

    x = params["hue"] + params["hueWidth"]
    if x > 179:
         x = 179
    high = np.array([x, params["high"], params["high"]])

    mask = cv2.inRange(hsv, low, high)
    return mask


def findLargestContour(source):
    contours, hierarchy = cv2.findContours(source, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) > 0:
        ordered = sorted(contours, key = cv2.contourArea, reverse = True)[:1]
        return ordered[0]

params = CVParameterGroup("Sliders")
params.addParameter("hue", 75, 255)
params.addParameter("hueWidth", 4, 25)
params.addParameter("FOV", 13782, 50000)
params.addParameter("low", 90, 255)
params.addParameter("high", 255, 255)
camera = cv2.VideoCapture(0)
#No camera's exposure goes this low, but this will set it as low as possible
camera.set(cv2.cv.CV_CAP_PROP_EXPOSURE,-100)
#camera.set(cv2.cv.CV_CAP_PROP_FPS, 15)
#camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
#camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)

fpsDisplay = False;
fpsCounter = WeightedFramerateCounter()
fpsInterval = RealtimeInterval(3.0)
raw = cv2.imread("testImages/1454372914.52.png")
targetSize = (20, 14)
while (True):
    #ret, raw = camera.read()
    
    ret = True
    if ret:
        fpsCounter.tick()
        
        #cv2.imshow("raw", raw)
        
        mask = filterHue(raw)
        cv2.imshow("mask", mask)

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
##            tPx = w
##            distance = params["FOV"]/w
##            cv2.putText(result, str(distance), (30, 30), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0,0,0), 1)

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
