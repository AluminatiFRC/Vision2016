import cv2

class CVParameterGroup:
    def __init__(self, windowName):
        self.windowName = windowName
        
    def addParameter(self, name, defaultValue, maxValue):
        cv2.createTrackbar(name, self.windowName, defaultValue, maxValue, lambda x: None)

    def showWindow(self):
        cv2.namedWindow(self.windowName)
        cv2.resizeWindow(self.windowName,420,420)

    def __getitem__(self, name):
        return cv2.getTrackbarPos(name, self.windowName)
    
    def __setitem__(self, name, value):
        cv2.setTrackbarPos(name, self.windowName, value)
