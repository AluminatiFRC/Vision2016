from WeightedFramerateCounter import WeightedFramerateCounter
from RealtimeInterval import RealtimeInterval
import numpy as np
import cv2

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
        cv2.imshow("raw", raw)
        fpsCounter.tick()
    
    if fpsDisplay and fpsInterval.hasElapsed():
        print "{0:.1f} fps".format(fpsCounter.getFramerate())
    
    keyPress = cv2.waitKey(1);
    if keyPress == ord('f'):
        fpsDisplay = not fpsDisplay
    elif keyPress == ord('q'):
        break 

camera.release()
cv2.destroyAllWindows()
