import cv2
cap = cv2.VideoCapture(0)
print "OpenCV version: " + cv2.__version__
while(True):
    ret, frame = cap.read()
    if ret:
        cv2.imshow('source', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
