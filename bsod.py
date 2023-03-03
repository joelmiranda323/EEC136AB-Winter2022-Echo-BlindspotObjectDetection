import jetson.inference
import jetson.utils
import threading
import RPi.GPIO as GPIO
import time

# Pin Definitions
leftTurn = 13      # Board pin 33 as left turn LED
leftSW = 7         # Board pin 26 as left switch

rightTurn =  4       # Board pin 07 as right turn LED
rightSW = 8          # Board pin 24 as right switch

warningLED = 22         # Board pin 15 as right warning LED

class csiCamera:
    def __init__(self):
        self.camNum = None
        self.net = None
        self.camera = None
        self.display = None
        self.img = None
        self.detection = None

    def openCam(self, camNum):
        try:
            print("\n\nOpenning Cam" + camNum + "\n\n")
            self.camNum = camNum
            self.net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)
            self.camera = jetson.utils.videoSource("csi://" + self.camNum)
            self.display = jetson.utils.videoOutput("display://" + self.camNum)
            self.img = self.camera.Capture()
	
        except RuntimeError:
            print("\n\n---Cannot open Cam" + camNum + "---\n\n")
            self.camNum = None
            self.net = None
            self.camera = None
            self.display = None

    def runThread(self):
        if self.camera != None and self.display != None:
            print("\n\nStarting thread for Cam" + self.camNum + "\n\n")
            self.thread = threading.Thread(target = self.detectObjects)
            self.thread.start()

    def detectObjects(self):
        objectsInBlindSpot = False
        self.img = self.camera.Capture()
        self.detections = self.net.Detect(self.img)
        if len(self.detections) != 0:
            objectsInBlindSpot = True
        self.display.Render(self.img)
        self.display.SetStatus("Cam" + self.camNum + " | Object Detection | Network {:.0f} FPS".format(self.net.GetNetworkFPS()))
        return objectsInBlindSpot
    
    def destroy(self):
        print("\n\nDestroying Cam"+ self.camNum + "\n\n")
        self.camNum = None
        self.net = None

        if self.camera.IsStreaming():
            self.camera.Close()
            self.camera = None

        if self.display.IsStreaming():
            self.display.Close()
            self.display = None
            
        self.img = None
        self.detection = None

def main():
    # Pin Setup:
    GPIO.setmode(GPIO.BCM)  # BCM pin-numbering scheme from Raspberry Pi
    GPIO.setup([leftTurn, rightTurn, warningLED], GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup([leftSW, rightSW], GPIO.IN)

    rightCam = csiCamera()
    rightCam.openCam("0")
    
    leftCam = csiCamera()
    leftCam.openCam("1")

    leftToggle = GPIO.LOW
    rightToggle = GPIO.LOW
    warningVal = GPIO.LOW

    print("\n\nProgram Ready!\n\n")
    try:
        while True:
            leftValue = GPIO.input(leftSW)
            rightValue = GPIO.input(rightSW)
            
            if not (leftValue == GPIO.HIGH and rightValue == GPIO.HIGH):
                # Left side of the vehicle
                if leftValue == GPIO.HIGH:
                    leftToggle ^= GPIO.HIGH
                    GPIO.output(leftTurn, leftToggle)
                    
                    if not leftCam.display.IsStreaming():
                        print("\nOpening display 1\n")
                        leftCam.display.Open()

                    leftObjectInBlindSpot = leftCam.detectObjects()
                    if leftObjectInBlindSpot and warningVal == GPIO.LOW:
                        warningVal = GPIO.HIGH
                    elif not leftObjectInBlindSpot and warningVal == GPIO.HIGH:
                        warningVal = GPIO.LOW
                    GPIO.output(warningLED, warningVal)
                else:
                    if leftToggle == GPIO.HIGH:
                        leftToggle = GPIO.LOW
                        GPIO.output(leftTurn, leftToggle)

                    if warningVal== GPIO.HIGH:
                        warningVal = GPIO.LOW
                        GPIO.output(warningLED, warningVal)
                    
                    if leftCam.display.IsStreaming():
                        print("\nClosing display 1\n")
                        leftCam.display.Close()

                # Right side of the vehicle
                if rightValue == GPIO.HIGH:
                    rightToggle ^= GPIO.HIGH
                    GPIO.output(rightTurn, rightToggle)
                    
                    if not rightCam.display.IsStreaming():
                        print("\nOpening display 0\n")
                        rightCam.display.Open()    
                   
                    rightobjectInBlindSpot = rightCam.detectObjects()
                    if rightobjectInBlindSpot and warningVal == GPIO.LOW:
                        warningVal = GPIO.HIGH
                    elif not rightobjectInBlindSpot and warningVal == GPIO.HIGH:
                        warningVal = GPIO.LOW
                    GPIO.output(warningLED, warningVal)    
                else:
                    if rightToggle == GPIO.HIGH:
                        rightToggle = GPIO.LOW
                        GPIO.output(rightTurn, rightToggle)

                    if warningVal== GPIO.HIGH:
                        warningVal = GPIO.LOW
                        GPIO.output(warningLED, warningVal)
                    
                    if rightCam.display.IsStreaming():
                        print("\nClosing display 0\n")
                        rightCam.display.Close()
                   
                time.sleep(0.125)
            else:
                GPIO.output(leftTurn, GPIO.LOW)
                GPIO.output(rightTurn, GPIO.LOW)
                GPIO.output(warningLED, GPIO.LOW)
                break
    finally:
        GPIO.cleanup()
        leftCam.destroy()
        rightCam.destroy()

if __name__ == '__main__':
    main()
