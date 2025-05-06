# -*- coding: utf-8 -*-
"""Control of Cameras

This script controls the cameras based on the comands by controll.py.
It consists of a CameraList class, a base-class and a seperate class for each indivual camera type.

Code for the individal classes is based from Dr. Kaspars Dadzis and was modified to fit an object oriented structure.
"""

import logging
import time
import os
import numpy as np
import matplotlib.pyplot as plt
from threading import Thread


class CameraList():
    """Creats a dict with all camera objects that should be used according to the config.yml"""
    def __init__(self, config):
        self.config        = config # General Config, not device specific
        self.stopThreads   = False
        self.cameraDict = {}

        # iterates thru devices and adds them to a dict
        for cameraName in self.config["cameras"]:
            if cameraName == "cam" and self.config["cameras"][cameraName]["skip"] == False:
                from devices.camera import VisCam
                self.visCam =   VisCam( cameraName, self.config["cameras"][cameraName])
                self.cameraDict.update({cameraName : self.visCam})

            if cameraName == "irCam" and self.config["cameras"][cameraName]["skip"] == False:
                from devices.camera import IrCam
                self.irCam =     IrCam( cameraName, self.config["cameras"][cameraName]) 
                self.cameraDict.update({cameraName : self.irCam})

            # Add new Camera here so it shows up in the dict

    
    def getCameraDict(self):
        return self.cameraDict
    

class Camera():
    """Base class for all Cameras
    
    args: 
        name:   string for naming device
        config: Config for specifc device
    """

    def __init__(self, name: str, config):
        self.testMode    = False
        self.stopThreads = False
        self.name        = name
        self.config      = config
        self.filename    = ""
        
        # if initCam() cant run successfully, a testmode is activated
        try:
            self.initCam()
            logging.info(f'{self.name}: Success.')
        except Exception as e:
            self.testMode = True
            logging.warning(f'{self.name}: Fail.\n------------\n{e}\n------------')

        # Cameras need a Thread to time automatic img taking 
        threadCamera = Thread(target=self.updateCameraThread)
        threadCamera.start()

    def initCam(self):
        # Override this function to init the Camera
        pass
    
    
    def getPicture(self):
        """takes a picture with camera"""
        if self.testMode == False:
            self.getFrame()
            logging.info(f"{self.name}: Picture was taken")
        else:
            logging.info(f"{self.name}: Picture was taken. TESTMODE. NO DATA WAS SEND TO CAMERA!")
    
    
    def getFrame(self):
        """Override this function to take a picture"""
        pass
    
    def getName(self):
        # Do not override
        return self.name
    
    def getFileName(self):
        # Do not override
        return self.filename
    
    def updateCamera(self):
        # Do not override
        # Function exist for backwards compability
        self.getPicture()

    def updateCameraThread(self):
        logging.info("started Camera thread")

        while self.stopThreads == False :
            self.updateCamera()
            for i in range(int(self.cameraSampletime/1000)): # wait 60 times 1 Second instead of one time for 60s to check closing condition more often
                if self.stopThreads == False:
                    time.sleep(0.99)
                else:
                    logging.info("finished Camera thread")
                    break

    def setStopThreads(self):
        # Do not override
        self.stopThreads = True



class IrCam(Camera):
    """Class for IR-Cam

    Cam is able to take pictures
    """

    def __init__(self, name, config):
        self.cameraSampletime = config["sampletime"]
        super().__init__(name, config)

    def initCam(self):
        # imports are local to enable simpler testing and reuse of code
        import busio
        import board
        import adafruit_mlx90640 # 2-wire I2C
        
        self.i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
        self.mlx = adafruit_mlx90640.MLX90640(self.i2c)
        self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
        
        # Prepare image save
        self.mlx_shape = (24,32)
        my_dpi=96
        self.figIR, self.axIR = plt.subplots(figsize=(400/my_dpi, 300/my_dpi), dpi=my_dpi)

        self.pltIR = self.axIR.imshow(np.zeros(self.mlx_shape),vmin=20,vmax=30) #start plot with zeros, cmap='Purples', 
        self.cbar  = self.figIR.colorbar(self.pltIR) # setup colorbar for temps
        self.cbar.set_label('Temperature [$^{\circ}$C]',fontsize=10) # colorbar label
        self.axIR.axis("off")
        self.figIR.tight_layout()
        self.lblmin = self.figIR.text(0.68, 0.06, '20.00' )
        self.lblmax = self.figIR.text(0.68, 0.91,  '30.00' )
        
    def getFrame(self):        
        mlx_val = np.zeros((24*32,)) # setup array for storing all 768 temperatures
        try:
            self.mlx.getFrame(mlx_val) # read MLX temperatures 
        except ValueError:
            logging.info('Error reading IR image!\n')
        else : # if sample was successfull
            data_array = (np.reshape(mlx_val, self.mlx_shape)) # reshape to 24x32
            
            data_min = np.min(data_array)
            data_max = np.max(data_array)
            self.pltIR.set_data(np.fliplr(data_array)) # flip left to right
            self.pltIR.set_clim(vmin=data_min,vmax=data_max) # set bounds
            self.cbar.mappable.set_clim(vmin=data_min,vmax=data_max)
            self.lblmin.set_text( str(round(data_min, 2)) )
            self.lblmax.set_text( str(round(data_max, 2)) )

            self.figIR.canvas.draw_idle()
            self.figIR.canvas.flush_events() 
                      
            fname = time.strftime("%Y%m%d-%H%M%S")
            self.filename    = "./data/IR_{:s}.jpg".format(fname)
            self.figIR.savefig(self.filename, bbox_inches='tight')
            
            """
            # Save raw Data
            fnamestrRaw = "./data/IR_{:s}.txt".format(fname)
            with open(fnamestrRaw, "a") as fileDAT:
                for line in np.fliplr(data_array):
                    fileDAT.write(str(line))
            """
            
            

class VisCam(Camera):
    """Control of the Pi Cam.
    
    Additional function: setting and getting exposure
    """
    def __init__(self, name, config):
        self.exposure_time = config["exp"]
        self.cameraSampletime = config["sampletime"]
        super().__init__(name, config)

    def initCam(self):
        # imports are local to enable simpler testing and reuse of code
        from picamera2 import Picamera2

        self.picam2 = Picamera2()
        self.picam2.set_logging(Picamera2.ERROR)
        CamConfig = self.picam2.create_still_configuration({"size": (1014, 760)}, raw=self.picam2.sensor_modes[2]) # Full sensor mode
        self.picam2.configure(CamConfig)
        os.environ["LIBCAMERA_LOG_LEVELS"] = "1" # 1 Info

    def getFrame(self):
        self.setExp(self.exposure_time)
        self.picam2.start(show_preview=False)
        time.sleep(0.2)
        fname = time.strftime("%Y%m%d-%H%M%S")
        self.filename = "./data/vis_{:s}.png".format(fname)
        self.picam2.capture_file(self.filename) # TODO: SET FILENAME

    def getExp(self):
        return self.exposure_time
    
    def setExp(self, exposure_time):
        """sets exposure time of the Camera"""
        self.exposure_time = exposure_time

        if self.testMode == False:
            self.picam2.controls.ExposureTime = self.exposure_time
            logging.info(f"{self.name}: Exposure Time was changed to {self.exposure_time}.")
        else:
            logging.info(f"{self.name}: Exposure Time was changed to {self.exposure_time}. TESTMODE. NO DATA WAS SEND TO CAMERA!")
