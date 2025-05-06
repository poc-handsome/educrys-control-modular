# -*- coding: utf-8 -*-
"""Internal view part of DemoCz

This file will recive data from control.py and will display them in a comand window.
If a input was reconginsed the input will be send to controll.py
"""

import cmd
import logging
from threading import Thread
import time


class View(cmd.Cmd):
    """do_* functions can be executed in the comand window"""

    def do_EOF(self, line):
        """Ends Programm"""
        self.setClosingEvent(True)
        time.sleep(0.5)
        return True

    def do_disp(self, line):
        """displays all Data"""
        print(f"Alarm in {self.alarmIn}s")
        for entry in self.completeTempList:
            try:
                print(f'{entry[0]:15}: {round(entry[1],2):6} [{entry[2]}]')
            except:
                print(f'{entry[0]:15}:    {entry[1]} [{entry[2]}]')

    # Comand to change liniear speeds of Motors
    def do_setLinSpeed(self, line):
        newSpeed = float(line.split(" ")[-1])
        self.setSpeed("linMotor", newSpeed)

    def do_setRotSpeed(self, line):
        newSpeed = float(line.split(" ")[-1])
        self.setSpeed("rotMotor", newSpeed)

    def do_setFanSpeed(self, line):
        newSpeed = float(line.split(" ")[-1])
        self.setSpeed("fan", newSpeed)

# Temperature
    # Comand to change Target Temperature
    def do_setTemp(self, line):
        try:
            newTargetTemp = float(line.split(" ")[-1])
            self.setTargetTemp(newTargetTemp)
        except Exception as e:
            print(f"invalid input: '{line}'. Choose 'PT1', 'TC1' or 'TC2'\n{e}")

    def do_setInputSensor(self, line):
        try:
            newInput = line.split(" ")[-1]
            self.setInputSensor(newInput)
        except Exception as e:
            print(f"invalid input: '{line}'. Choose 'PT1', 'TC1' or 'TC2'\n{e}")
    
# liniear position
    def do_setLinPos(self, line):
        try:
            newPos = float(line.split(" ")[-1])
            self.setPos(newPos)
        except:
            print(f"invalid input: '{line}'")
    
# tare weight
    def do_tare(self, line):
        self.setTare(True)

# Camera 
    def do_setExp(self, line):
        """Change Exposure
        TODO: check valid inputs
        """
        try:
            newExp = int(line.split(" ")[-1])
        except:
            print(f"invalid input: '{line}'")
            newExp = self.exp
        self.setExp(newExp)

    def do_takePic(self, line):
        try:
            cameraName = line.split(" ")[-1]
        except:
            print(f"invalid input: '{line}'")
            cameraName = ""

        if cameraName == "vis":
            self.setTakePicVis(True)
        elif cameraName == "ir":
            self.setTakePicIr(True)
        else:
            print("Choose 'vis' or 'ir'")

# LED
    def do_toggleLED(self, line):
        self.setToggleLED(True)

# Alarm
    def do_toggleAlarm(self, line):
        self.setToggleBuzzer(True)
    
    def do_setAlarmIn(self, line):
        alarmIn = float(line.split(" ")[-1])
        self.setAlarmIn(alarmIn)
    
# BACKGROUND FUNCTIONS ------------------------------------------------------------------------------------------------
    """These Functions do not get executed by the comand window. 
    The Functions are necceary Controll the Input and Outputs to and from Controll.py
    """
    
# SPEED
    def getSpeed(self, motorName):
        return self.motorDataDict.get(motorName)

    def setSpeed(self, motorName, newSpeed):
        self.motorDataDict[motorName] = newSpeed
    
    def setSpeedDataDict(self, newMotorDataDict):
        self.motorDataDict = newMotorDataDict

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
    def getToggleManual(self):
        return self.toggleManual
    
    def setToggleManual(self, newToggle):
        self.toggleManual = newToggle

# TARE
    def getTare(self):
        return self.tare

    def setTare(self, newTare):
        self.tare = newTare

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
        return self.takePictureVis

    def setTakePicVis(self, newVal):
        self.takePictureVis = newVal

# takePictureIr
    def getTakePicIr(self):
        return self.takePictureIr

    def setTakePicIr(self, newVal):
        self.takePictureIr = newVal

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
    

# OTHER FUNCTIONS
    # including an __init__ function leads to errors, so this function will be called externaly and serve as an init function
    def start(self, config):
        self.config = config
        self.setPos(self.config["motors"]["linMotor"]["pos"]["start"])
        self.setExp(self.config["cameras"]["cam"]["exp"])
        self.setClosingEvent(False)
        self.setTargetTemp(0)
        self.setTare(False)
        self.setTakePicVis(False)
        self.setTakePicIr(False)
        self.setToggleLED(False)
        self.setToggleBuzzer(False)
        self.setAlarmIn(0)
        self.inputSensor = "PT1"
        self.toggleManual = False

        threadViewStart  = Thread(target=self.startGuiThread)
        threadViewStart.start()

    # refereshes Data. Gets called by Controller
    def updateGui(self, motorDataDict, completeTempList):
        self.motorDataDict  = motorDataDict
        self.completeTempList = completeTempList

    # Starts the comand window
    def startGuiThread(self):
        logging.info("starting View thread")
        self.cmdloop()
        logging.info("finished View thread")


