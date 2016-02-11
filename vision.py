import paho.mqtt.client as mqtt
import numpy as np
import cv2

control = "Control"

cap = cv2.VideoCapture(-1)
cv2.namedWindow(control)
cv2.resizeWindow(control,640,480)
cap.set(cv2.cv.CV_CAP_PROP_EXPOSURE,-10)

params = { 'low': 68, 'high':78, 'ED Size': 5}

def mkAdjuster(name):
    def adjust(value):
        params[name] = value
    return adjust
    
for param in params:    
    cv2.createTrackbar(param,control,params[param],255,mkAdjuster(param))

client = mqtt.Client()
client.connect("roboRIO-5495-FRC.local", 5888)

while(True):
    #client.publish("5495.mqttTest", "r u reciving?")
    # Capture frame-by-frame
    ret, frame = cap.read()
    if ret is False:
        continue

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    channels = cv2.split(hsv)
    frame = cv2.inRange(hsv[0], params['low'], params['high']) 

    cv2.imshow('mask', frame)
    
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

