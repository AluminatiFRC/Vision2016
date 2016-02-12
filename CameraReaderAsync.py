from threading import Thread

class CameraReaderAsync:
    def __init__(self, videoSource):
        self.__source = camera
        self.Start()
        
    def __ReadAsync(self):
        while True:
            if self.__stopRequested:
                return
            (self.__validFrame, self.__frame) = self.__source.read()
            if self.__validFrame:
                self.__lastFrameRead = False

    def Start(self):
        self.__lastFrameRead = False
        self.__frame = None
        self.__stopRequested = False
        self.__validFrame = False
        Thread(target=self.__ReadAsync).start()
        
    def Stop(self):
        self.__stopRequested = True

    # Return a frame if we have a new frame since this was last called.
    # If there is no frame or if the frame is not new, return None.
    def Read(self):
        if not self.__validFrame || self.__lastFrameRead:
            return None

        self.__lastFrameRead = True
        return self.__frame

    # Return the last frame read even if it has been retrieved before.
    # Will return None if we never read a valid frame from the source.
    def ReadLastFrame(self):
        return self.__frame
        
