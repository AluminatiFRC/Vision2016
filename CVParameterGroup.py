import cv2

class CVParameterGroup:
    def __init__(self, windowName, show = False):
        self.values = {}
        self.show = show
        self.paramCount = 0
        self.windowName = windowName
        if self.show:
            cv2.namedWindow(self.windowName)
            self.__resizeWindow()
        
    def addParameter(self, name, defaultValue, maxValue):
        self.values[name] = defaultValue
        if self.show:
            self.paramCount += 1
            cv2.createTrackbar(name, self.windowName, defaultValue, maxValue, lambda x: None)
            self.__resizeWindow()

    def __getitem__(self, name):
        if self.show:
            return cv2.getTrackbarPos(name, self.windowName)
        if name in self.values:
            return self.values[name]
        return -1
    
    def __setitem__(self, name, value):
        self.values[name] = value
        cv2.setTrackbarPos(name, self.windowName, value)

    def __resizeWindow(self):
        height = 0
        if not self.paramCount:
            height = 76
        else:
            height = self.paramCount * 19
        cv2.resizeWindow(self.windowName, 500, height)
