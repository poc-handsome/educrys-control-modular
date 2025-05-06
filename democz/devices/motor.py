# -*- coding: utf-8 -*-
"""Control Of Motors

This script controls the motors based on the comands by controll.py.
It consists of a MotorList class, a base-class and a seperate class for each indivual motor type.

The MotorList class creates the motors and makes them callable. The individual classes control one motor type and inherits from the base class.
Every motor has a speed. The linear motor has a speed and calculated position.

Code for the individal classes is based from Dr. Kaspars Dadzis and was modified to fit an object oriented structure.
"""

import logging
import time
from threading import Thread

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except Exception as e:
    logging.warning(f"missing imports: {e}")

class MotorList():
    """Creats a dict with all motor objects that should be used according to the config.yml"""
    def __init__(self, config):
        self.config    = config
        self.motorDict = {} # Stors the motor objects
        self.dataDict  = {} # Stors the data from motors

        for motorName in self.config["motors"]:
            
            if motorName == "linMotor" and self.config["motors"][motorName]["skip"] == False:
                #from devices.motor import LinMotor
                self.linMotor = LinMotor(motorName, self.config["motors"][motorName])
                self.motorDict.update(     { motorName : self.linMotor } )
                self.dataDict.update( { motorName : 0             } ) # Start Speed is always 0

            elif motorName == "rotMotor" and self.config["motors"][motorName]["skip"] == False:
                #from devices.motor import RotMotor
                self.rotMotor = RotMotor(motorName, self.config["motors"][motorName])
                self.motorDict.update(     { motorName : self.rotMotor } )
                self.dataDict.update({motorName : 0}) # Start Speed is always 0
            
            elif motorName == "fan" and self.config["motors"][motorName]["skip"] == False:
                #from devices.motor import Fan
                self.fan = Fan(motorName, self.config["motors"][motorName])
                self.motorDict.update( { motorName : self.fan } )
                self.dataDict.update({motorName : 0}) # Start Speed is always 0
    
    def getData(self):
        return self.motorDict, self.dataDict

class Motor():
    """Base class for all Motors.
    All Motors have a Speed.
    
    args: 
        name:   string for naming device
        config: Config for specifc device
    """
    def __init__(self, name: str, config):
        self.testMode = False
        self.name     = name
        self.config   = config

        # Speeds
        self.speed    = 0
        self.minSpeed = self.config["speed"]["min"]
        self.maxSpeed = self.config["speed"]["max"]

        try:
            self.initMotor()
            logging.info(f'{self.name:10}: Success.')
        except Exception as e:
            self.testMode = True
            logging.warning(f'{self.name:10}: Fail.\n------------\n{e}\n------------')

    def initMotor(self):
        # Override this function to init the sensor
        pass
    
    # Do not override
    def getName(self):
        return self.name

    # Do not override
    def read(self):
        self.updateData()
        returnData = []
        for data in self.data:
            returnData.append(data)
        return returnData

    
    def updateData(self):
        """dict that saves current data points of motor as well as names and units."""
        # Override. put data dict here
        pass

    ### SPEED FUNCTIONS
    # Do not override
    def setSpeed(self, newSpeed: float):
        """changes speed if newSpeed is inside min/max values and motor is not in testmode."""
        if newSpeed >= self.minSpeed and newSpeed <= self.maxSpeed:
            self.speed = newSpeed
            if self.testMode == False:
                try:
                    self.setMotor()
                    logging.info(f'{self.name}: Changed of speed to {self.speed}.')
                    return 1
                except Exception as e:
                    logging.info(f'{self.name}: Change of speed to {self.speed} not possible.\n{e}')
                    return -1
            else:
                logging.info(f'{self.name}: Changed of speed to {self.speed}. TESTMODE ACTIVE. NO COMAND WAS SEND TO MOTOR!')
                return 1
        else:
            logging.warning(f"{self.name}: Changed of speed to {newSpeed} not possible, above max or below min Value. minSpeed:{self.minSpeed}, maxSpeed:{self.maxSpeed}")
            return -1

    # override this function to set speed of motor
    def setMotor(self):
        pass
    
    # Do not override
    def getSpeed(self):
        return self.speed

    # override this function to close motor
    def __del__(self):
        pass



class LinMotor(Motor):
    """Class for Linear Motor

    Motor has a speed and a calculated position value.
    """

    def __init__(self, name: str, config):
        super().__init__(name, config)
        self.stopThreads     = False
        self.motorSampletime = self.config["sampletime"]

        threadMotors = Thread(target=self.updateMotorThread)
        threadMotors.start()

    def updateData(self):
        """dict that saves current data points of motor as well as names and units."""
        self.data = [{"name": "LinSpeed", "val" : self.getSpeed(), "unit": "mm/min"}, {"name": "LinPos", "val" : self.getPos(), "unit": "mm",}]

    def initMotor(self):
        # pins
        self.pinPwm = self.config["pins"]["pwm"]
        self.pinDir = self.config["pins"]["dir"]
        self.pinOn  = self.config["pins"]["on_" ]

        # pos
        self.posStart = self.config["pos"]["start"]
        self.pos      = self.posStart
        self.posMin   = self.config["pos"]["min"]
        self.posMax   = self.config["pos"]["max"]
        
        self.motLinFreq = 0

        GPIO.setup( self.pinDir, GPIO.OUT)
        GPIO.output(self.pinDir, GPIO.LOW)
        
        GPIO.setup( self.pinOn, GPIO.OUT)
        GPIO.output(self.pinOn, GPIO.LOW)

        from rpi_hardware_pwm import HardwarePWM
        self.pwm_lin = HardwarePWM(pwm_channel=1, hz=100, chip=0)
        self.pwm_lin.start(0)

    def setMotor(self):
        """implements the speed control"""
        if self.speed == 0:
            GPIO.output(self.pinOn, GPIO.LOW)
            self.pwm_lin.change_duty_cycle(0)
        else :
            self.motLinFreq = 5.0 * abs(self.speed) #* 8.33 # with HW PWM  
            if self.motLinFreq > 1500 : self.motLinFreq = 1500

            GPIO.output(self.pinOn, GPIO.HIGH)

            self.pwm_lin.change_duty_cycle(50)
            self.pwm_lin.change_frequency(self.motLinFreq)

        # Set Direction:
        if self.speed > 0 :
            GPIO.output(self.pinDir, GPIO.HIGH)
        else :
            GPIO.output(self.pinDir, GPIO.LOW)

    # position
    def setPos(self, newPos: float):
        self.pos = newPos
    
    def getPos(self):
        return self.pos

    def getMinMax(self):
        return [self.posMin, self.posMax]
    
    def setStopThreads(self):
        self.stopThreads = True

    def updateMotor(self):
        """calculate linear position"""
        self.pos += self.getSpeed() * self.motorSampletime/1000/60

    def updateMotorThread(self):
        """Thread is needed to calculate the dutycycle of the motor"""
        logging.info("Motor thread started")

        while self.stopThreads == False :
            self.updateMotor()
            time.sleep(self.motorSampletime/1000)  
        logging.info("finished Motor thread")
        
    def __del__(self):
        """will automaticly close the object"""
        if self.testMode == False:
            self.pwm_lin.stop()
            #GPIO.output(self.pinOn, GPIO.LOW)
        logging.info(f"{self.name:10}: Stopped")



class RotMotor(Motor):
    """Class for Rotation/DC Motor

    Motor has a speed value.
    """

    def __init__(self, name: str, config):
        super().__init__(name, config)
    
    def updateData(self):
        """dict that saves current data points of motor as well as names and units."""
        self.data = [{"name": "RotSpeed", "val" : self.getSpeed(), "unit": "RPM",}]

    def initMotor(self):
        from rpi_hardware_pwm import HardwarePWM
        self.pinPwm = self.config["pins"]["pwm"]
        self.pinDir = self.config["pins"]["dir"]

        GPIO.setup(self.pinDir, GPIO.OUT)
        GPIO.output(self.pinDir, GPIO.LOW)

        self.pwm_rot = HardwarePWM(pwm_channel=0, hz=20000, chip=0)
        self.pwm_rot.start(0)

    # Speed Function
    def setMotor(self):
        """implements the speed control"""
        if self.speed == 0:
                self.pwm_rot.change_duty_cycle(0)
        else :
            # motRotDuty = 3.178 * abs(rot_val) + 1.130 # rpm to %
            motRotDuty = 0.83 * 11.0 * abs(self.speed)
            #if abs(rot_val) < 3 : motRotDuty = 0 # does not rotate smoothly
            if motRotDuty > 100 : motRotDuty = 100
            
            self.pwm_rot.change_duty_cycle(motRotDuty)

        if self.speed>0 :
            GPIO.output(self.pinDir, GPIO.LOW)
        else :
            GPIO.output(self.pinDir, GPIO.HIGH)

    def __del__(self):
        """will automaticly close the object"""
        if self.testMode == False:
            self.pwm_rot.stop()
            GPIO.output(self.pinDir, GPIO.LOW)
        logging.info(f"{self.name:10}: Stopped")



class Fan(Motor):
    """Class for Fan Motor

    Motor has a speed value.
    """
    def __init__(self, name: str, config):
        super().__init__(name, config)

    def updateData(self):
        """dict that saves current data points of motor as well as names and units."""
        self.data = [{"name": "FanSpeed",  "val" : self.getSpeed(), "unit": "%",}]

    def initMotor(self):
        self.pin = self.config["pin"]

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        
        self.pwm_fan = GPIO.PWM(self.pin, 250) 
        self.pwm_fan.start(0)

    def setMotor(self):
        """implements the speed control"""
        if self.speed == 0 : motFanDuty = 0
        else : motFanDuty = abs(self.speed ) 
        
        if motFanDuty > 100 : motFanDuty = 100

        self.pwm_fan.ChangeDutyCycle(motFanDuty)

    def __del__(self):
        """will automaticly close the object"""
        if self.testMode == False:
            self.pwm_fan.stop()
            GPIO.output(self.pin, GPIO.LOW)
        logging.info(f"{self.name:10}: Stopped")
