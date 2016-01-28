import numpy as np
import cv2

control = "Control"

cap = cv2.VideoCapture(0)
cv2.namedWindow(control)
cv2.resizeWindow(control,640,480)

params = { 'Low': 44, 'High':49, 'ED Size': 5}

def mkAdjuster(name):
    def adjust(value):
        params[name] = value
    return adjust
    
for param in params:    
    cv2.createTrackbar(param,control,params[param],255,mkAdjuster(param))

while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()
    cv2.imshow('Raw', frame)

    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)

    channels = cv2.split(frame)

    frame = cv2.inRange(channels[0], params['Low'], params['High'])
    

    size = max(1,params['ED Size'])
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,  (size, size))
    frame = cv2.erode(frame, kernel)
    frame = cv2.dilate(frame, kernel)

    # Display the resulting frame
    cv2.imshow('frame',frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
