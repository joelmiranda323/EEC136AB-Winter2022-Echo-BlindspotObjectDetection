import jetson.inference
import jetson.utils
import threading
import RPi.GPIO as GPIO
import time

# Pin Definitions

# Left side
leftTurn = 25           # Board pin 22 as left turn LED
leftWarningLED = 9      # Board pin 21 as left warning LED
leftSW = 10             # Board pin 19 as left switch

# Right side
rightTurn =  23         # Board pin 16 as right turn LED
rightWarningLED = 22    # Board pin 15 as right warning LED
rightSW = 27            # Board pin 13 as right switch

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
    # GPIO Pin Setup:
    GPIO.setmode(GPIO.BCM)  # BCM pin-numbering scheme from Raspberry Pi
    GPIO.setup([leftTurn, leftWarningLED, rightTurn, rightWarningLED], GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup([leftSW, rightSW], GPIO.IN)

    # Setup left Camera
    leftCam = csiCamera()
    leftCam.openCam("1")

    # Setup right Camera
    rightCam = csiCamera()
    rightCam.openCam("0")

    # Initial state for left LEDs
    leftToggle = GPIO.LOW
    leftWarningVal = GPIO.LOW

    # Initial state for right LEDs
    rightToggle = GPIO.LOW
    rightWarningVal = GPIO.LOW

    print("\n\nProgram Ready!\n\n")
    try:
        while True:
            # Read left and right switch inputs
            leftValueSW = GPIO.input(leftSW)
            rightValueSW = GPIO.input(rightSW)
            
            # Start polling if either switch is ON
            # Stop the progam if both switches are ON
            if not (leftValueSW == GPIO.HIGH and rightValueSW == GPIO.HIGH):
                
                ### Left side of the vehicle ###
                # Driver is signaling to the left
                if leftValueSW == GPIO.HIGH:

                    # Toggle RED led to mimic a turn signal
                    leftToggle ^= GPIO.HIGH
                    GPIO.output(leftTurn, leftToggle)
                    
                    # Open the camera to capture frames
                    if not leftCam.camera.IsStreaming():
                        leftCam.camera.Open()
                        print("\Camera 1 is open\n")

                    # Open the GUI to display camera frames
                    if not leftCam.display.IsStreaming():
                        leftCam.display.Open()
                        print("\nDisplay 1 is open\n")
                        
                    # Detect objects for the current frame
                    leftObjectInBlindSpot = leftCam.detectObjects()

                    # Singal the driver by turing ON the YELLOW LED
                    # if an object is detected in the current frame 
                    # else keep the YELLOW LED off
                    if leftObjectInBlindSpot and leftWarningVal == GPIO.LOW:
                        leftWarningVal = GPIO.HIGH
                    elif not leftObjectInBlindSpot and leftWarningVal == GPIO.HIGH:
                        leftWarningVal = GPIO.LOW
                    GPIO.output(leftWarningLED, leftWarningVal)
                else:
                    # Driver is NOT signaling to the left
                    # Turn OFF the RED LED
                    if leftToggle == GPIO.HIGH:
                        leftToggle = GPIO.LOW
                        GPIO.output(leftTurn, leftToggle)

                    # Turn OFF the YELLOW LED
                    if leftWarningVal== GPIO.HIGH:
                        leftWarningVal = GPIO.LOW
                        GPIO.output(leftWarningLED, leftWarningVal)

                    # Close the camera to stop capturing frames
                    if leftCam.camera.IsStreaming():
                        leftCam.camera.Close()
                        print("\nCamera 1 is closed\n")

                    # Close the GUI to stop displaying frames
                    if leftCam.display.IsStreaming():
                        leftCam.display.Close()
                        print("\nDisplay 1 is closed\n")

                # Right side of the vehicle
                if rightValueSW == GPIO.HIGH:
                    rightToggle ^= GPIO.HIGH
                    GPIO.output(rightTurn, rightToggle)

                    if not rightCam.camera.IsStreaming():
                        rightCam.camera.Open()
                    
                    if not rightCam.display.IsStreaming():
                        rightCam.display.Open()    
                   
                    rightobjectInBlindSpot = rightCam.detectObjects()
                    if rightobjectInBlindSpot and rightWarningVal == GPIO.LOW:
                        rightWarningVal = GPIO.HIGH
                    elif not rightobjectInBlindSpot and rightWarningVal == GPIO.HIGH:
                        rightWarningVal = GPIO.LOW
                    GPIO.output(rightWarningLED, rightWarningVal)    
                else:
                    if rightToggle == GPIO.HIGH:
                        rightToggle = GPIO.LOW
                        GPIO.output(rightTurn, rightToggle)

                    if rightWarningVal== GPIO.HIGH:
                        rightWarningVal = GPIO.LOW
                        GPIO.output(rightWarningLED, rightWarningVal)
                    
                    if rightCam.camera.IsStreaming():
                        rightCam.camera.Close()
                        print("\nCamera 0 is closed\n")
                    
                    if rightCam.display.IsStreaming():
                        rightCam.display.Close()
                        print("\nDisplay 0 is closed\n")

                time.sleep(0.125)
            else:
                # Turn OFF all LEDs
                GPIO.output(leftTurn, GPIO.LOW)
                GPIO.output(leftWarningLED, GPIO.LOW)
                GPIO.output(rightTurn, GPIO.LOW)
                GPIO.output(rightWarningLED, GPIO.LOW)
                break
    finally:
        
        # Reset GPIOs and destroy the cameras
        GPIO.cleanup()
        leftCam.destroy()
        rightCam.destroy()

if __name__ == '__main__':
    main()
