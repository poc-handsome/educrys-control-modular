import time
from threading import Thread
import logging
import json # https://stackoverflow.com/questions/15190362/sending-a-dictionary-using-sockets-in-python

#import serial
import socket

class SocketMock():
    def __init__(self):
        pass

    def sendall(self, data):
        logging.debug(f"Data: '{data}' TESTMODE: NO DATA SEND!")

    def recv(self, bytes):
        return -1

class InterfaceGui:
    def __init__(self):
        self.stopThreads = False
        self.stopThreadsInternal = False
        self.sleeptime = 0.05
        
        # Concection
        host = "localhost"
        port = 55555
        self.guiData = {}

        # Sensor
        self.pt1     = 0
        self.tc1     = 0
        self.tc2     = 0
        self.env     = 0
        self.hum     = 0
        self.weight  = 0
        self.kwh     = 0
        self.current = 0
        self.tare    = False

        # Motor
        self.linSpeed = 0
        self.rotSpeed = 0
        self.fanSpeed = 0
        self.pos      = 100

        # Devices
        self.toggleLED    = False
        self.toggleBuzzer = False
        self.alarmIn      = 0

        # PID
        self.inputSensor = 0
        self.pidMode     = 0
        self.pidoutMan   = 0
        self.targetTemp  = 0

        # Heating
        self.kwh        = False
        self.powerReset = False

        # Camera
        self.exp = 0

        self.takePicVis = False
        self.takePicIr  = False
        

        self.s    = self.initConnection(host, port+0)
        time.sleep(1)
                
        
        self.sVis = self.initConnection(host, port+1)
        time.sleep(1)
        
        self.sIr  = self.initConnection(host, port+2)
        #self.config = json.loads(self.s.recv(1024).decode()) # get Config
        
        Thread(target=self.loop).start()
        Thread(target=self.loopImg).start()
        

    def initConnection(self, host, port):
        for i in range(5): # retrying 5 times before using serial Mock
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                logging.info("Connection to DemoCz Succefuly.")
                break;
            except Exception as e:
                if i == 9:
                    logging.error(f"Connection to DemoCz not possable.\n{e}")
                    s = SocketMock()
                else:
                    logging.warning(f"{i}: Connection failed, Trying to reconect in 1 second. DemoCz needs to start up fully before connection is possible.")
                    time.sleep(1)
        return s
    
    def getConfig(self):
        return self.config         

    def loop(self):
        logging.info("Loop started")
        while self.stopThreadsInternal == False:
            self.readData()
            self.writeData()
            time.sleep(self.sleeptime)
        logging.info("Loop finished")
    
    def loopImg(self):
        logging.info("loopImg started")
        while self.stopThreadsInternal == False:
            self.readImgData()
            time.sleep(self.sleeptime)
        logging.info("loopImg finished")

    def writeData(self):
        self.functions = {
            "linSpeed"     : self.linSpeed,
            "rotSpeed"     : self.rotSpeed,
            "fanSpeed"     : self.fanSpeed,
            "linPos"       : self.pos,
            "tare"         : self.tare,
            "powerReset"   : self.powerReset,
            "toggleLed"    : self.toggleLED,
            "toggleBuzzer" : self.toggleBuzzer,
            "alarmIn"      : self.alarmIn,
            "targetTemp"   : self.targetTemp,
            "exp"          : self.exp,
            "takePicVis"   : self.takePicVis,
            "takePicIr"    : self.takePicIr,
            "stopThreads"  : self.stopThreads
        }

        self.s.sendall(json.dumps(self.functions).encode())
        
        # Set Toggle Functions to False 
        self.toggleLED    = False
        self.toggleBuzzer = False
        self.tare         = False
        self.powerReset   = False
        self.takePicVis   = False
        self.takePicIr    = False
        
    def readImgData(self):
        # Quelle: https://stackoverflow.com/questions/8994937/send-image-using-socket-programming-python
        strng = self.sVis.recv(1024)
        if not strng:
            pass # Check if Pic gets send then open file
        else:
            fp = open('latestVis.png','wb')
            fp.write(strng)
            while True:
                strng = self.sVis.recv(1024)
                if not strng:
                    fp.close()
                    logging.info("Reciving Vis Picture Complete")
                    break
                else: fp.write(strng)


        strng = self.sIr.recv(1024)
        if not strng:
            pass # Check if Pic gets send then open file
        else:
            fp = open('latestIr.jpg','wb')
            fp.write(strng)
            while True:
                strng = self.sIr.recv(1024)
                if not strng:
                    fp.close()
                    logging.info("Reciving Ir Picture Complete")
                    break
                else: fp.write(strng)
            
    def readData(self):
        try:
            self.guiData = json.loads(self.s.recv(1024).decode())
            #logging.info(f'Serial data received:\n{self.guiData}')
        except Exception as e:
            logging.error(f"Errorin reciving Data:\n{e}")

    def setGuiData(self, newData):
        self.guiData = newData

    def getGuiData(self):
        return self.guiData
    
### Functions for Buttons ### ### ### ### ### ### ### ### ### ### ### ### ### ### 

# Speed
    def getLinSpeed(self):
        return self.linSpeed

    def setLinSpeed(self, newSpeed):
        self.linSpeed = newSpeed

    def getRotSpeed(self):
        return self.rotSpeed

    def setRotSpeed(self, newSpeed):
        self.rotSpeed = newSpeed

    def getFanSpeed(self):
        return self.fanSpeed

    def setFanSpeed(self, newSpeed):
        self.fanSpeed = newSpeed

# Linear Position
    def getPos(self):
        return self.pos

    def setPos(self, newPos):
        self.pos = newPos

# TARGET TEMP
    def getTargetTemp(self):
        return self.targetTemp

    def setTargetTemp(self, newTargetTemp):
        self.targetTemp = newTargetTemp

# Input Sensor
    def getInputSensor(self):
        return self.inputSensor

    def setInputSensor(self, newInput):
        self.inputSensor = newInput

# Manual Input
    def getPidMode(self):
        return self.togglePidMode
    
    def setPidMode(self, newToggle):
        self.togglePidMode = newToggle

# TARE
    def getTare(self):
        return self.tare

    def setTare(self, newTare):
        self.tare = newTare

#Power
    def getPowerReset(self):
        return self.powerReset

    def setPowerReset(self, newValue):
        self.powerReset = newValue

# CLOSING EVENT
    def setClosingEvent(self, stopThreads):
        self.stopThreads = stopThreads
    
    def getClosingEvent(self):
        return self.stopThreads
    
    def setClosingEventInternal(self, stopThreadsInternal):
        self.stopThreadsInternal = stopThreadsInternal
    
# Exposure
    def getExp(self):
        return self.exp

    def setExp(self, newExp):
        self.exp = newExp

# takePicVis
    def getTakePicVis(self):
        return self.takePicVis

    def setTakePicVis(self, newVal):
        self.takePicVis = newVal

# takePicIr
    def getTakePicIr(self):
        return self.takePicIr

    def setTakePicIr(self, newVal):
        self.takePicIr = newVal

# LED
    def getToggleLED(self):
        return self.toggleLED

    def setToggleLED(self, newVal):
        self.toggleLED = newVal

# Buzzer
    def getToggleBuzzer(self):
        return self.toggleBuzzer

    def setToggleBuzzer(self, newVal):
        self.toggleBuzzer = newVal

    def getAlarmIn(self):
        return self.alarmIn
    
    def setAlarmIn(self, newAlarmIn):
        self.alarmIn = newAlarmIn

# PID Out Man
    def setPidOutMan(self, newVal):
        self.pidoutMan = newVal
        logging.error("not implemented!")

    def getPidOutMan(self):
        return self.pidoutMan
        logging.error("not implemented!")
