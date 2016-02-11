import time

class RealtimeInterval:
    def __init__(self, intervalInSeconds, allowImmediate = True):
        self.interval = intervalInSeconds
        self.allowImmediate = allowImmediate
        self.reset()

    def reset(self):
        if self.allowImmediate:
            self.startTime = 0
        else:
            self.startTime = time.time()
        
    def hasElapsed(self):
        timeNow = time.time()
        elapsed = timeNow - self.startTime
        if (elapsed >= self.interval):
            self.startTime = timeNow;
            return True
