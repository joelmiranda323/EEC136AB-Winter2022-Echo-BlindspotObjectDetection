import jetson.inference
import jetson.utils
import threading

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
            self.camNum = camNum
            self.net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)
            self.camera = jetson.utils.videoSource("csi://" + self.camNum)
            self.display = jetson.utils.videoOutput("display://" + self.camNum)
        
        except RuntimeError:
            print("Cannot open Cam" + camNum)
            self.camNum = None
            self.net = None
            self.camera = None
            self.display = None

    def runThread(self):
        if self.camera != None and self.display != None:
            self.thread = threading.Thread(target = self.detectObjects)
            self.thread.start()

    def detectObjects(self):
        while self.display.IsStreaming():
            self.img = self.camera.Capture()
            self.detection = self.net.Detect(self.img)
            self.display.Render(self.img)
            self.display.SetStatus("Cam" + self.camNum + " | Object Detection | Network {:.0f} FPS".format(self.net.GetNetworkFPS()))

    def stopThread(self):
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
    rightCam = csiCamera()
    rightCam.openCam("0")
    
    leftCam = csiCamera()
    leftCam.openCam("1")
    
    rightCam.runThread()
    leftCam.runThread()

    if rightCam.display != None and leftCam.display != None:
        while rightCam.display.IsStreaming() and leftCam.display.IsStreaming():
    
    rightCam.stopThread()
    rightCam.freeSpace()
    
    leftCam.stopThread() 
    leftCam.freeSpace()

syncCamDet()
