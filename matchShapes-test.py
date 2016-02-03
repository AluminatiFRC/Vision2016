from WeightedFramerateCounter import WeightedFramerateCounter
from RealtimeInterval import RealtimeInterval
from CVParameterGroup import CVParameterGroup
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

params = CVParameterGroup("Sliders")
params.addParameter("hue", 111, 255)
params.addParameter("hueWidth", 2, 25)
params.addParameter("FOV", 13782, 50000)

camera = cv2.VideoCapture(0)
#camera.set(cv2.cv.CV_CAP_PROP_FPS, 15)
#camera.set(cv2.cv.CV_CAP_PROP_FOCUS_AUTO, 0)
#camera.set(cv2.cv.CV_CAP_PROP_EXPOSURE_AUTO, 0)
#camera.set(cv2.cv.CV_CAP_PROP_EXPOSURE, 0)
#camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
#camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)

fpsDisplay = False;
fpsCounter = WeightedFramerateCounter()
fpsInterval = RealtimeInterval(3.0)

raw = cv2.imread("pi-logo.png")
mask = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
mask = cv2.GaussianBlur(mask, (5, 5), 0)
mask = cv2.Canny(mask, 100, 200)
largestContour = findLargestContour(mask)
baselineShape = None
if largestContour is not None:
    baselineShape = largestContour
    cv2.imshow("mask", mask)
    cv2.drawContours(raw, largestContour, -1, (0, 255, 0), 3)
    cv2.imshow("basline", raw)

while (True):
    ret, raw = camera.read()
    if ret:
        fpsCounter.tick()
        
        mask = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        mask = cv2.Canny(mask, 100, 200)

        result = raw.copy()

        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            if cv2.contourArea(c) > 200:
                rank = cv2.matchShapes(baselineShape, c, 1, 0.0)
                if rank <= 0.05:
                    #if rank <= 0.01:
                    #    baselineShape = c
                    cv2.drawContours(result, c, -1, (0, 255, 0), 3)

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
