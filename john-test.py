from WeightedFramerateCounter import WeightedFramerateCounter
from RealtimeInterval import RealtimeInterval
import numpy as np
import cv2

def filterHue(source):
    hsv = cv2.cvtColor(source, cv2.COLOR_BGR2HSV)
    x = params["hue"] - params["hueWidth"]
    if x < 0:
         x = 0
    low = np.array([x, 50, 50])

    x = params["hue"] + params["hueWidth"]
    if x > 179:
         x = 179
    high = np.array([x, 255, 255])

    mask = cv2.inRange(hsv, low, high)
    return mask


def findLargestContour(source):
    contours, hierarchy = cv2.findContours(source, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) > 0:
        ordered = sorted(contours, key = cv2.contourArea, reverse = True)[:1]
        return ordered[0]

params = { "hue": 111, "hueWidth": 8 }#, "gray": 80}

def mkAdjuster(name):
    def adjust(value):
        params[name] = value
    return adjust

control = "sliders"
cv2.namedWindow(control);
for param in params:
    if param == "hue":
        cv2.createTrackbar(param,control,params[param],179,mkAdjuster(param))
    if param == "hueWidth":
        cv2.createTrackbar(param,control,params[param],20,mkAdjuster(param))
    else:
        cv2.createTrackbar(param,control,params[param],255,mkAdjuster(param))

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
        
        mask = filterHue(raw)
        #cv2.imshow("mask", mask)

        #colorOnly = cv2.bitwise_and(raw, raw, mask = mask)
        #cv2.imshow("colormasked", colorOnly)
        #mask = cv2.threshold(mask, params["gray"], 255, 0)

        result = raw.copy()
        largestContour = findLargestContour(mask)
        if largestContour is not None:
            M = cv2.moments(largestContour)
            if M["m00"] != 0:
                cx = int(M["m10"]/M["m00"])
                cy = int(M["m01"]/M["m00"])
                cv2.circle(result, (cx, cy), 8, (250, 250, 250), -1)
                hull = cv2.convexHull(largestContour)
                for i in range(hull.shape[0]-1):
                    cv2.line(result, tuple(hull[i][0]), tuple(hull[i+1][0]), (255, 255, 0), 2)

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
