# -*- coding: utf-8 -*-
"""Control Of Devices

This script controls the devices based on the comands by control.py.
It consists of a DeviceList class, seperate classes for each indivual device type.
Devices are actuators that are not motors.

Code for the individal classes is based from Dr. Kaspars Dadzis and was modified to fit an object oriented structure.
"""

import logging
from threading import Thread
import time

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except Exception as e:
    logging.warning(f"missing imports: {e}")


class DeviceList():
    """Creats a device-objects that should be used according to config. Makes then accaccible for the controll.py"""
    def __init__(self, config):
        self.config = config

        for deviceName in self.config["devices"]:
            if deviceName == "buzzer" and self.config["devices"][deviceName]["skip"] == False:
                self.buzzer = Buzzer("buzzer", 13)
            if deviceName == "led" and self.config["devices"][deviceName]["skip"] == False:
                self.led = Led("led", 24)

    def getBuzzer(self):
        try:
            return self.buzzer
        except:
            pass
    
    def getLed(self):
        try:
            return self.led
        except:
            pass



class Buzzer():
    def __init__(self, name, pin):
        self.testMode       = False
        self.stopThreads    = False
        self.name           = name
        self.pin            = pin
        self.state          = False
        self.alarmIn        = 0
        self.sound_freq     = 250
        self.sound_duty     = 0
        self.sound_freq_old = 0
        self.sound_duty_old = 0
        self.lasttime_sound = time.time_ns()

        try:
            self.threadTone = Thread(target=self.setOutputThread)
            self.threadTone.start()

            GPIO.setup(self.pin, GPIO.OUT)
            GPIO.output(self.pin, GPIO.LOW)
            logging.info(f'{self.name}: Success.')
        except Exception as e:
            self.testMode = True
            logging.warning(f'{self.name}: Fail.\n------------\n{e}\n------------')
    
    def getState(self):
        return self.state

    def setState(self, newState):
        self.state = newState
    
    def getAlarmIn(self):
        return self.alarmIn

    def setAlarmIn(self, newTime):
        self.alarmIn = newTime

    def setOutputThread(self):
        logging.info("start Buzzer thread")
        while self.stopThreads == False:
            self.setOutput()
            
            time.sleep(0.2)
        logging.info("finished Buzzer thread")

    def setOutput(self):
        if self.alarmIn != 0: self.alarmIn -= 0.2 
        if self.alarmIn < 0:
            self.state = True
            self.alarmIn = 0

        if self.state == True :
            now = time.time_ns() 
            time_sound = now - self.lasttime_sound
            if time_sound > 0 and time_sound < 1000000000 :          self.sound_duty = 50
            if time_sound > 1000000000 and time_sound < 2000000000 : self.sound_duty = 0
            if time_sound > 2000000000 : self.lasttime_sound = now
        else :
            self.sound_duty = 0

        # sound
        if self.sound_freq != self.sound_freq_old or self.sound_duty != self.sound_duty_old :
            if self.testMode == False:
                if self.sound_duty == 0 : GPIO.output(self.pin, GPIO.LOW)
                else : GPIO.output(self.pin, GPIO.HIGH)
            else:
                logging.info("sound_freq={:.2f} sound_duty={:.2f}. TESTMODE. NO DATA WAS SEND!".format(self.sound_freq, self.sound_duty))
            self.sound_freq_old = self.sound_freq
            self.sound_duty_old = self.sound_duty
        else:
            pass
    
    def setStopThreads(self):
        self.stopThreads = True

class Led():
    def __init__(self, name, pin):
        self.testMode = False
        self.name     = name
        self.pin      = pin
        self.state    = False

        try:
            GPIO.setup(self.pin, GPIO.OUT)
            GPIO.output(self.pin, GPIO.LOW)
            logging.info(f'{self.name}: Success.')
        except Exception as e:
            self.testMode = True
            logging.warning(f'{self.name}: Fail.\n------------\n{e}\n------------')
    
    def getState(self):
        return self.state
        
    def setState(self, newState):
        self.state = newState

    # do not override
    def setOutput(self, newState):
        self.state = newState
        if self.state == True:

            if self.testMode == False:
                GPIO.output(self.pin, GPIO.HIGH)
                logging.info(f"{self.name}: Device was turned on.")
            else:
                logging.info(f"{self.name}: Device was turned on. TESTMODE. NO DATA WAS SEND TO DEVICE!")

        else:
            if self.testMode == False:
                GPIO.output(self.pin, GPIO.LOW)
                logging.info(f"{self.name}: Device was turned off.")
            else:
                logging.info(f"{self.name}: Device was turned off. TESTMODE. NO DATA WAS SEND TO DEVICE!")
