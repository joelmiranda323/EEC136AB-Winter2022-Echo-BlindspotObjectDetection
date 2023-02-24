import jetson.inference
import jetson.utils
import threading

class csiCamera:
    def __init__(self):
        ## Camera Initialization
        self.camNum = None
        self.net = None
        self.camera = None
        self.display = None
        self.img = None
        self.detection = None
        
        ## Thread Initialization
        self.thread = None
        self.threadLock = threading.Lock()
        self.threadRunning = False

    def openCam(self, camNum):
        try:
            self.camNum = camNum
            self.net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)
            self.camera = jetson.utils.videoSource("csi://" + self.camNum)
            self.display = jetson.utils.videoOutput("display://" + self.camNum)
        
        except RuntimeError:
            self.camNum = None
            self.net = None
            self.camera = None
            self.display = None
            print("Cannot open Cam" + camNum)

    def runThread(self):
        if self.threadRunning:
            print("Already running detectObjects thread on Cam" + self.camNum)
            return None
        
        if self.camera != None and self.display != None:
            self.threadRunning = True
            self.thread = threading.Thread(target = self.detectObjects)
            self.thread.start()
        return self

    def detectObjects(self):
        while self.threadRunning and self.display.IsStreaming():
            try:
                with self.threadLock:
                    self.img = self.camera.Capture()
                    self.detection = self.net.Detect(self.img)
                    self.display.Render(self.img)
    
                    self.display.SetStatus("Cam" + self.camNum + " | Object Detection | Network {:.0f} FPS".format(self.net.GetNetworkFPS()))

            except RuntimeError:
                print('Could not read image from camera')

    def stopThread(self):
        self.threadRunning = False
        self.thread.join()
        self.thread = None
    
    def freeSpace(self):
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
        
        if self.thread != None:
            self.thread.join()
            self.thread = None

def syncCamDet():
    left_cam = csiCamera()
    left_cam.openCam("1")

    right_cam = csiCamera()
    right_cam.openCam("0")

    left_cam.runThread()
    right_cam.runThread()

    while True:
        if not left_cam.display.IsStreaming() and left_cam.threadRunning:
            left_cam.stopThread()

        if not right_cam.display.IsStreaming() and right_cam.threadRunning:
            right_cam.stopThread()

        if not left_cam.threadRunning and not right_cam.threadRunning:
            break

    left_cam.freeSpace()
    right_cam.freeSpace()