# Calculate the distance to an object of known size.
# We need to know the perceived focal length for this to work.
#
# Known Focal Length values for calibrated cameras
#   Logitech C920:              620
#   Microsoft Lifecam HD-3000:  ???
#
class TriangleSimilarityDistanceCalculator:
    knownSize = 0
    focalLength = 0;

    def __init__(self, knownSize, perceivedFocalLength = None):
        self.knownSize = knownSize
        self.focalLength = perceivedFocalLength

    # Call this to calibrate a camera and then use the calibrated focalLength value
    # when using this class to calculate real distances.
    def CalculatePerceivedFOVAtGivenDistance(self, perceivedSize, distance):
        focalLength = perceivedSize * distance / float(self.knownSize)
        return focalLength

    # This will return the real world distance of the known object.
    def CalcualteDistance(self, perceivedSize):
        if self.focalLength == None:
            raise ValueError("Did you forget to calibrate this camera and set the perceived focal length?")
        distance = self.knownSize * self.focalLength / float(perceivedSize)
        return distance
