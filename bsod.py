import jetson.inference
import jetson.utils
import threading
import RPi.GPIO as GPIO
import time

# Pin Definitions
leftTurn = 13      # Board pin 33 as left turn LED
leftSW = 7         # Board pin 26 as left switch
leftWarning = 10   # Board pin 19 as left warining LED

rightTurn =  4       # Board pin 07 as right turn LED
rightSW = 8          # Board pin 24 as right switch
rightWarning = 22    # Board pin 15 as right warning LED


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
        self.img = self.camera.Capture()
        self.detection = self.net.Detect(self.img)
        self.display.Render(self.img)
        self.display.SetStatus("Cam" + self.camNum + " | Object Detection | Network {:.0f} FPS".format(self.net.GetNetworkFPS()))
    
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
    GPIO.setup([leftTurn, rightTurn], GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup([leftSW, rightSW], GPIO.IN)

    rightCam = csiCamera()
    rightCam.openCam("0")
    
    leftCam = csiCamera()
    leftCam.openCam("1")

    print("\n\nProgram Ready!\n\n")
    leftToggle = GPIO.LOW
    rightToggle = GPIO.LOW
    try:
        while True:
            leftValue = GPIO.input(leftSW)
            rightValue = GPIO.input(rightSW)
            if not (leftValue == GPIO.HIGH and rightValue == GPIO.HIGH):
                if leftValue == GPIO.HIGH:
                    leftToggle ^= GPIO.HIGH
                    GPIO.output(leftTurn, leftToggle)
                    if not leftCam.display.IsStreaming():
                        print("\nOpening display\n")
                        leftCam.display.Open()
                    leftCam.detectObjects()
                else:
                    leftToggle = GPIO.LOW
                    GPIO.output(leftTurn, leftToggle)
                    if leftCam.display.IsStreaming():
                        print("\nClosing display\n")
                        leftCam.display.Close()

                if rightValue == GPIO.HIGH:
                    rightToggle ^= GPIO.HIGH
                    GPIO.output(rightTurn, rightToggle)
                    if not rightCam.display.IsStreaming():
                        print("\nOpening display\n")
                        rightCam.display.Open()
                    rightCam.detectObjects()
                else:
                    rightToggle = GPIO.LOW
                    GPIO.output(rightTurn, rightToggle)
                    if rightCam.display.IsStreaming():
                        print("\nClosing display\n")
                        rightCam.display.Close()
                   
                time.sleep(0.5)
            else:
                GPIO.output(leftTurn, GPIO.LOW)
                #GPIO.output(leftWarning, GPIO.LOW)
                GPIO.output(rightTurn, GPIO.LOW)
                #GPIO.output(rightWarning, GPIO.LOW)
                break
    finally:
        GPIO.cleanup()
        leftCam.destroy()
        rightCam.destroy()

if __name__ == '__main__':
    main()