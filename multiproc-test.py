import cv2
import CameraReaderAsync

# Initialize
debugMode = True
camera = cv2.VideoCapture(0)
camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
cameraReader = CameraReaderAsync.CameraReaderAsync(camera)

# Main Loop
framesToProcess = 60 * 5
while debugMode or framesToProcess >= 0:
    raw = cameraReader.Read()
    if raw is not None:
        framesToProcess -= 1
        if debugMode:
            cv2.imshow("raw", raw)

    if debugMode:
        keyPress = cv2.waitKey(1)
        if keyPress == ord("q"):
            break
    
# Cleanup
cameraReader.Stop()
camera.release()
cv2.destroyAllWindows()
