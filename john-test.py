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
    
def clickHandler(event, x, y, flags, param):
    global points, boxSource
    
    if event == cv2.EVENT_LBUTTONDOWN:
        if points < 4:
            boxSource[points] = (x, y)
            points += 1
    elif event == cv2.EVENT_RBUTTONDOWN:
        points = 0
    
params = CVParameterGroup("Sliders")
params.addParameter("hue", 107, 255)
params.addParameter("hueWidth", 7, 25)
params.addParameter("FOV", 13782, 50000)
params.addParameter("low", 134, 255)
params.addParameter("high", 255, 255)
params.addParameter("keystone", 0, 640/2)
camera = cv2.VideoCapture(0)
#No camera's exposure goes this low, but this will set it as low as possible
camera.set(cv2.cv.CV_CAP_PROP_EXPOSURE,-100)
#camera.set(cv2.cv.CV_CAP_PROP_FPS, 15)
#camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
#camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)

objHeight = 10.5;
objWidth = 14.0;
objAspect = objWidth / objHeight

fpsDisplay = False;
fpsCounter = WeightedFramerateCounter()
fpsInterval = RealtimeInterval(3.0)
raw = cv2.imread("1454660931.58.png")
targetSize = (20, 14)

points = 4
boxSource = [[0, 0], [640, 0], [640, 480], [0, 480]]

cv2.namedWindow("result")
#cv2.setMouseCallback("result", clickHandler)

while (True):
    ret, raw = camera.read()
    
    ret = True
    if ret:
        fpsCounter.tick()
        
        cv2.imshow("raw", raw)
        
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
            
            rect = cv2.minAreaRect(largestContour)
            box = cv2.cv.BoxPoints(rect);
            box = np.int0(box);
            cv2.drawContours(result, [box], 0, (0, 192, 0), 2)           
            #cv2.drawContours(result, [largestContour], 0, (0, 127, 127), 2)           

            hull = cv2.convexHull(largestContour)
            cv2.drawContours(result, [hull], 0, (127, 0, 255), 2)

            x,y,w,h = cv2.boundingRect(largestContour)
            center = (x+(w/2), y+(h/2))
            cv2.rectangle(result, (x,y), (x+w,y+h), (40,0,120), 2)

            if points == 4:
                width = 640;
                height = 480;

##                ptSrc = np.float32([boxSource[:3]]);
##                ptDst = np.float32([[params['keystone'], 0], [width-params['keystone'], 0], [width+params['keystone'], height]]);
##                amatrix = cv2.getAffineTransform(ptSrc, ptDst)
##                transformed = cv2.warpAffine(raw, amatrix, (width, height))
##                cv2.imshow("transformed", transformed)
                
                ptSrc = np.float32([boxSource]);
                ptDst = np.float32([[params['keystone'], 0], [width-params['keystone'], 0], [width + params['keystone'], height], [-params['keystone'], height]]);
                matrix = cv2.getPerspectiveTransform(ptSrc, ptDst)
                transformed = cv2.warpPerspective(raw, matrix, (int(width), int(height)))
                cv2.imshow("transformed", transformed)
#            else:
#                for i in range(points):
#                    cv2.circle(result, boxSource[i], 2, (255, 255, 255), 1)
                    
##            if points == 4:
##                width = 400;
##                height = width * objAspect;
##                ptSrc = np.float32([boxSource]);
##                ptDst = np.float32([[0, 0], [width, 0], [width, height], [0, height]]);
##                matrix = cv2.getPerspectiveTransform(ptSrc, ptDst)
##                transformed = cv2.warpPerspective(raw, matrix, (int(width), int(height)))
##                cv2.imshow("transformed", transformed)
##            else:
##                for i in range(points):
##                    cv2.circle(result, boxSource[i], 2, (255, 255, 255), 1)
            
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
