import jetson.inference
import jetson.utils
import RPi.GPIO as GPIO
import time

######################
# Pin Definitions
######################
# Left side
leftTurn = 25           # Board pin 22 as left turn LED
leftWarningLED = 9      # Board pin 21 as left warning LED
leftSW = 10             # Board pin 19 as left switch

# Right side
rightTurn =  23         # Board pin 16 as right turn LED
rightWarningLED = 22    # Board pin 15 as right warning LED
rightSW = 27            # Board pin 13 as right switch

######################
# CSI camera object
######################
class csiCamera:
    def __init__(self):
        self.camNum = None
        self.net = None
        self.camera = None
        self.display = None
        self.img = None
        self.detection = None

    def configCam(self, camNum):
        try:
            # Save the port number where the camera is connected to
            self.camNum = camNum
            # Specify the Jetson object detection model
            self.net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)
            # Specify the csi port number
            self.camera = jetson.utils.videoSource("csi://" + self.camNum)
            # Specify the GUI display linking to the camera port number
            self.display = jetson.utils.videoOutput("display://" + self.camNum)
            # Capture the first frame so the camera is ready
            self.img = self.camera.Capture()
        except RuntimeError:
            print("\n\n CANNOT OPEN Cam" + camNum + "\n\n")
            self.camNum = None
            self.net = None
            self.camera = None
            self.display = None

    def detectObjects(self):
        # Initally no objects are detected
        objectsInBlindSpot = False
        # Caputure the next frame on the camera
        self.img = self.camera.Capture()
        # Check for objects in the frame/image
        self.detections = self.net.Detect(self.img)
        if len(self.detections) != 0:
            objectsInBlindSpot = True
        # Display the frame/image and FPS on the GUI display
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

######################
# Helper functions
######################
# Toggle a specific pin channel	
def toggleLED(turnChannel, toggleChannel):
    toggleChannel ^= GPIO.HIGH
    GPIO.output(turnChannel, toggleChannel)

# Turn OFF a specific channel if its ON
def turnOffGPIO(channel, val):
    if val == GPIO.HIGH:
        val = GPIO.LOW
        GPIO.output(channel, val)

# If the camera is not capturing frame then
# open it so it can caputure frames and
# display it on the GUI display
def openCamDis(camObj):
    if not camObj.camera.IsStreaming():
        camObj.camera.Open()
    if not camObj.display.IsStreaming():
	    camObj.display.Open()

# If the camera is currently capturing frames 
# then close it to stop caputuring frames and
# stop displaying frames	
def closeCamDis(camObj):
	if camObj.camera.IsStreaming():
		camObj.camera.Close()
	if camObj.display.IsStreaming():
		camObj.display.Close()

# Detect objects on the current frame
#
# Turn ON the the warning LED if an object
# is detected and the warning LED is OFF
# or turn OFF the warning LED if no object 
# is detected and the warning LED is ON
def warningNotif(camObj, warningChannel, warningVal):
	objectInBlindSpot = camObj.detectObjects()

	if objectInBlindSpot and warningVal == GPIO.LOW:
		warningVal = GPIO.HIGH
	elif not objectInBlindSpot and warningVal == GPIO.HIGH:
		warningVal = GPIO.LOW
	GPIO.output(warningChannel, warningVal)

######################
# Main funciton
######################
def main():
    # GPIO Pin Setup:
    GPIO.setmode(GPIO.BCM)  # BCM pin-numbering scheme from Raspberry Pi
    GPIO.setup([leftTurn, leftWarningLED, rightTurn, rightWarningLED], GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup([leftSW, rightSW], GPIO.IN)

    # Setup left Camera
    leftCam = csiCamera()
    leftCam.configCam("1")

    # Setup right Camera
    rightCam = csiCamera()
    rightCam.configCam("0")

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
                    toggleLED(leftTurn, leftToggle)

                    # Open the camera to capture frames and
                    # Open the GUI to display camera frames
                    openCamDis(leftCam)

                    # Detect objects for the current frame and
                    # singals the driver by turing ON the YELLOW
                    # LED if an object is detected in the current
                    # frame, else keep the YELLOW LED OFF
                    warningNotif(leftCam, leftWarningLED, leftWarningVal)
                else:
                    # Driver is NOT signaling to the left
                    # Turn OFF the RED LED
                    turnOffGPIO(leftTurn, leftToggle)

                    # Turn OFF the YELLOW LED
                    turnOffGPIO(leftWarningLED, leftWarningVal)

                    # Close the camera to stop capturing frames and
                    # Close the GUI to stop displaying frames
                    closeCamDis(leftCam)
                    
                # Check Blindspot on the right side of the vehicle
                if rightValueSW == GPIO.HIGH:
                    toggleLED(rightTurn, rightToggle)
                    openCamDis(rightCam)
                    warningNotif(rightCam, rightWarningLED, rightWarningVal)   
                else:
                    # Driver is NOT signaling to the right
                    turnOffGPIO(rightTurn, rightToggle)
                    turnOffGPIO(rightWarningLED, rightWarningVal)
                    closeCamDis(rightCam)
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