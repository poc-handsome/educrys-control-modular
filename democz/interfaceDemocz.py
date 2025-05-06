# -*- coding: utf-8 -*-
"""Connection to external GUI

This file will send and recive data to the externaly started GUI. The GUI has a simular class so that Data can be exchanged.
"""
import time
from threading import Thread
import logging
import socket
import json

class InterfaceDemocz:
    def __init__(self, config):
        self.config      = config
        self.stopThreads = False
        self.sleeptime   = 0.05

        # Conection to GUI
        self.host = self.config["userInterfaces"]["gui"]
        self.port = 55555  # Port to listen on (non-privileged ports are > 1023)
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
        self.powerReset = False

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
        self.pidSel    = 0
        self.pidMode   = 0
        self.pidoutMan = 0
        self.targetTemp = 0

        # Heating
        self.kwh = False

        # Camera
        self.exp = 0

        self.takePicVis = False
        self.takePicIr  = False

        # Connections for normal Data and Camaeras are seperated to ensure a free link at all times
        self.conn    = self.initConnection(self.port+0)
        self.connVis = self.initConnection(self.port+1)
        self.connIr  = self.initConnection(self.port+2)
        #self.conn.sendall(json.dumps(self.config).encode()) # TODO: Send Config to other Gui
        Thread(target=self.loop).start()
        Thread(target=self.loopImg).start()
        

    def initConnection(self, port):
        # source: https://realpython.com/python-sockets/
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", port)) 
        server_socket.listen(1) # wait for GUI
        conn, address = server_socket.accept()
        logging.info(address)
        return conn
        
    # Loops are needed to time functions precicly and stop them if the program should shut down
    def loop(self):
        """Loop for Sensor&Motor Data"""
        logging.info("Loop started")
        while self.stopThreads == False:
            self.writeData()
            self.readData()
            time.sleep(self.sleeptime)
        logging.info("Loop finished")
        
    def loopImg(self):
        """Loop for all image Data"""
        logging.info("loopImg started")
        while self.stopThreads == False:
            self.writeImgData()
            time.sleep(self.sleeptime)
        logging.info("loopImg finished")

    def writeData(self):
        """Data that is send to GUI"""
        self.conn.sendall(json.dumps(self.guiData).encode())
        logging.debug(f"send Data: {self.guiData}")
        
    def writeImgData(self):
        """Image data that is send to GUI
        Contains all Cam data
        """
        # source: https://stackoverflow.com/questions/8994937/send-image-using-socket-programming-python
        # Send Vis Pic ### ### ### ### ### ### ### ### ### ### ### ### 
        if self.takePicVis == True and self.visFilename != "" :
            try:
                img = open(self.visFilename,'rb')
                while True:
                    strng = img.read(1024)
                    if not strng: break
                    self.connVis.send(strng)
                img.close()
                self.takePicVi = False
                logging.info("Sending Vis Picture Complete")
            except Exception as e:
                logging.error(f"Sending Vis Picture to GUI not possible\n{e}")
        
        # Send Ir Pic ### ### ### ### ### ### ### ### ### ### ### ### 
        if self.takePicIr == True and self.irFilename != "" :
            try:
                img = open(self.irFilename,'rb')
                while True:
                    strng = img.read(1024)
                    if not strng: break
                    self.connIr.send(strng)
                img.close()
                self.takePicIr = False
                logging.info("Sending IR Picture Complete")
            except Exception as e:
                logging.error(f"Sending IR Picture to GUI not possible\n{e}")
        

    def readData(self):
        """Data from GUI"""
        try:
            self.functions = json.loads(self.conn.recv(1024).decode())
            logging.debug(f'Serial data received:\n{self.functions}')
        except Exception as e:
            logging.error(f"Error in reading Data:\n{e}")
            self.functions = {}

        # store data from GUI externaly accessiable variables.
        self.linSpeed = self.functions.get("linSpeed")
        self.rotSpeed = self.functions.get("rotSpeed")
        self.fanSpeed = self.functions.get("fanSpeed")
        self.pos      = self.functions.get("linPos")

        self.tare       = self.functions.get("tare")
        self.powerReset = self.functions.get("powerReset")
        
        self.toggleLED   = self.functions.get("toggleLed")
        self.toggleBuzzer = self.functions.get("toggleBuzzer")
        self.alarmIn     = self.functions.get("alarmIn")

        self.takePicVis = self.functions.get("takePicVis")
        if self.takePicVis == True: time.sleep(2) 
        self.takePicIr  = self.functions.get("takePicIr")

        self.targetTemp = self.functions.get("targetTemp")
        
        # give control.py enough time to start closing.
        if self.functions.get("stopThreads") == True:
                logging.info("stopThreads recived")
                self.stopThreads = True
                time.sleep(2)
    
    def setGuiData(self, newData):
        self.guiData = newData

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
    
# Exposure
    def getExp(self):
        return self.exp

    def setExp(self, newExp):
        self.exp = newExp

# takePictureVis
    def getTakePicVis(self):
        return self.takePicVis

    def setTakePicVis(self, newVal):
        self.takePicVis = newVal
        
    def sendVisPic(self, fname):
        # source: https://stackoverflow.com/questions/8994937/send-image-using-socket-programming-python
        img = open(fname,'r')
        while True:
            strng = img.readline(512)
            if not strng: break
            self.conn.send(strng)
        img.close()

# takePictureIr
    def getTakePicIr(self):
        return self.takePicIr

    def setTakePicIr(self, newVal):
        self.takePicIr = newVal

# Filenames
    def setVisFilename(self, newVal):
        self.visFilename = newVal
        
    def setIrFilename(self, newVal):
        self.irFilename = newVal

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
