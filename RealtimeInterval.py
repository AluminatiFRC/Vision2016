import time

class RealtimeInterval:
    startTime = 0
    interval = 0

    def __init__(self, intervalInSeconds):
        self.startTime = time.time()
        self.interval = intervalInSeconds

    def start(self):
        self.startTime = time.time()
        
    def hasElapsed(self):
        timeNow = time.time()
        if self.startTime == 0:
            self.startTime = timeNow
            return False
    
        elapsed = timeNow - self.startTime
        if (elapsed >= self.interval):
            self.startTime = timeNow;
            return True
