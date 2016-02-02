from WeightedFramerateCounter import WeightedFramerateCounter
from RealtimeInterval import RealtimeInterval
from CVParameterGroup import CVParameterGroup
import numpy as np
import cv2

def hsvFilter(source):
    hsv = cv2.cvtColor(source, cv2.COLOR_BGR2HSV)

    hsvcomponents = cv2.split(hsv)

    low = np.array([params["hue low"], params["sat low"], params["value low"]])
    high = np.array([params["hue high"], params["sat high"], params["value high"]])

    mask = cv2.inRange(hsv, low, high)
    return mask


def findLargestContour(source):
    contours, hierarchy = cv2.findContours(source, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) > 0:
        ordered = sorted(contours, key = cv2.contourArea, reverse = True)[:1]
        return ordered[0]

params = CVParameterGroup("Sliders")
params.addParameter("hue high", 106, 255)
params.addParameter("hue low", 0, 255)
params.addParameter("sat high", 75, 255)
params.addParameter("sat low", 0, 255)
params.addParameter("value high", 255, 255)
params.addParameter("value low", 105, 255)
params.addParameter("ED Size", 4, 20)

camera = cv2.VideoCapture(0)
#camera.set(cv2.cv.CV_CAP_PROP_FPS, 15)
#camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
#camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)

fpsDisplay = False;
fpsCounter = WeightedFramerateCounter()
fpsInterval = RealtimeInterval(3.0)

while (True):
    ret, raw = camera.read()
    if ret:
        fpsCounter.tick()
        
        #cv2.imshow("raw", raw)
        
        mask = hsvFilter(raw)
        cv2.imshow("mask", mask)

        size = max(1,params['ED Size'])
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,  (size, size))
        mask = cv2.erode(mask, kernel)
        mask = cv2.dilate(mask, kernel)
        cv2.imshow("Erosion", mask)
        
        result = raw.copy()
        largestContour = findLargestContour(mask)
        if largestContour is not None:
            M = cv2.moments(largestContour)
            if M["m00"] != 0:
                cx = int(M["m10"]/M["m00"])
                cy = int(M["m01"]/M["m00"])
                cv2.circle(result, (cx, cy), 8, (250, 250, 250), -1)
                hull = cv2.convexHull(largestContour)
                cv2.drawContours(result, [hull], 0, (0,255,0), 3)
            x,y,w,h = cv2.boundingRect(largestContour)
            cv2.rectangle(result, (x,y), (x+w,y+h), (40,0,120), 2)
            tPx = w
            distance = params["FOV"]/w
            cv2.putText(result, str(distance), (30, 30), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0,0,0), 1)

        cv2.imshow("result", result)
    
    if fpsDisplay and fpsInterval.hasElapsed():
        print "{0:.1f} fps".format(fpsCounter.getFramerate())
    
    keyPress = cv2.waitKey(1)
    if keyPress == ord("f"):
        fpsDisplay = not fpsDisplay
    elif keyPress == ord("q"):
        break 
    elif keyPress == ord("z"):
        cv2.imwrite("working.png", raw)
        print "Took screenshot"

camera.release()
cv2.destroyAllWindows()
