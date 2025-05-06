# -*- coding: utf-8 -*-
"""Control Of Sensors

This script controls the sensors based on the comands by control.py.
It consists of a SensorList class, a base-class and a seperate class for each indivual sensor type.

The SensorList class creates the sensors and makes them callable. The individual classes control one snesors type and inherits from the base class.
Every has at least one value.

Code for the individal classes is based from Dr. Kaspars Dadzis and was modified to fit an object oriented structure.
"""

import logging
import time
from random import random
from threading import Thread

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    import digitalio
    import busio
    import adafruit_max31865 # 4-wire SPI: SDI/MOSI, SDA/MISO, CLK, CS
    import adafruit_max31856 # 4-wire SPI
    import board
except Exception as e:
    logging.warning(f"missing imports: {e}")


class SensorList:
    def __init__(self, config):
        """Creats a list with all sensor objects that should be used according to the config.yml"""
        self.sensorList = []
        self.config = config

        for sensorName in self.config["sensors"]:
            if sensorName == "ptSensor" and self.config["sensors"][sensorName]["skip"] == False:
                self.sensorList.append(PtSensor(sensorName, self.config["sensors"][sensorName]) )

            if sensorName[:-1] == "tcSensor" and self.config["sensors"][sensorName]["skip"] == False:
                self.sensorList.append(TcSensor(sensorName, self.config["sensors"][sensorName]) )

            if sensorName == "weight" and self.config["sensors"][sensorName]["skip"] == False:
                self.weight = Weight(sensorName, self.config["sensors"][sensorName]) # has a fuction ("Button") so object must be callable
                self.sensorList.append(self.weight)
            
            if sensorName == "environment" and self.config["sensors"][sensorName]["skip"] == False:
                self.sensorList.append(Environment(sensorName, self.config["sensors"][sensorName]) )
            
            if sensorName == "power" and self.config["sensors"][sensorName]["skip"] == False:
                self.sensorList.append(Power(sensorName, self.config["sensors"][sensorName]) )
    
    def getWeightSensor(self):
        # this sensors needs a extra function because it is the only sensor with callable function: calibrate()
        try:
            return self.weight
        except:
            pass
    
    def getSensorList(self):
        return self.sensorList



class Sensor():
    """Base class for all Sensors.
    All Sensors have at least one value to read.
    
    args: 
        name:   string for naming device
        config: Config for specifc device
    """
    def __init__(self, name, config):
        
        self.testMode = False
        self.name     = name
        self.config   = config
        self.data     = []
        
        try:
            self.initSensor()
            logging.info(f'{self.name:10}: Success.')
        except Exception as e:
            self.testMode = True
            logging.warning(f'{self.name:10}: Fail.\n{e}\n------------')

    # Override this function to init the sensor
    def initSensor(self):
        pass
    
    # Do not override
    def getName(self):
        return self.name
    
    def calibrate(self):
        # can be overridden to calibrate device
        pass

    ### FUNCTIONS FOR DATA GENERATION
    # Do not override
    def read(self):
            self.updateData()
            returnData = []
            for data in self.data:
                #data["val"] = self.sample()[0] 
                returnData.append(data)
            return returnData
    
    # Override. Put data dict here
    def updateData(self):
        """dict that saves current data points of motor as well as names and units."""
        pass
    
    # Override this to return the current value of the sensor
    def sample(self):
        return -1

    # Can be override with fitting random value generation for the test mode.
    def randomValues(self):
        return -2

class PtSensor(Sensor):
    def __init__(self, name, config):
        super().__init__(name, config)
    
    def updateData(self):
        """dict that saves current data points of motor as well as names and units."""
        if self.testMode == False: self.data = [{"name": "PT1", "val" : self.sample()      , "unit": "deg",}]
        else:                      self.data = [{"name": "PT1", "val" : self.randomValues(), "unit": "deg",}]

        
        self.Tcorrection = self.config["TCorrection"]

    # function to init the sensor 
    def initSensor(self):
        self.spi = board.SPI()
        self.pin = board.D17
        pt1_cs = digitalio.DigitalInOut(self.pin) 
        self.pt1 = adafruit_max31865.MAX31865(self.spi, pt1_cs) #+ self.Tcorrection

    # return the current value of the sensor
    def sample(self):
        dataList = self.pt1.temperature
        return dataList

    # fitting random value generation
    def randomValues(self):
        dataList = round(random()*10,2)
        return dataList

class TcSensor(Sensor):
    def __init__(self, name, config):
        super().__init__(name, config)
        
    def updateData(self):
        """dict that saves current data points of motor as well as names and units."""
        if self.testMode == False: self.data = [{"name": self.DataName, "val" : self.sample()      , "unit": "deg",}]
        else:                      self.data = [{"name": self.DataName, "val" : self.randomValues(), "unit": "deg",}]
                
    # function to init the sensor
    def initSensor(self):
        
        self.DataName = self.config["name"]
        if self.DataName == "TC1":
            self.pin = board.D22
        elif self.DataName == "TC2":
            self.pin = board.D27
        else:
            logging.error("Name of tcSensor-name has to be 'TC1' or 'TC2'!")
        
        self.spi = board.SPI()
        tc_cs = digitalio.DigitalInOut(self.pin) 
        self.tc = adafruit_max31856.MAX31856(self.spi, tc_cs)
        

    # return the current value of the sensor
    def sample(self):
        return self.tc.temperature

    # fitting random value generation
    def randomValues(self):
        dataList = round(random()*10,2)
        return dataList



class Weight(Sensor):
    def __init__(self, name, config):
        super().__init__(name, config)

    def updateData(self):
        """dict that saves current data points of motor as well as names and units."""
        if self.testMode == False: self.data = [{"name": "Weight", "val" : self.sample()      , "unit": "g",}]
        else:                      self.data = [{"name": "Weight", "val" : self.randomValues(), "unit": "g",}]


    # function to init the sensor
    def initSensor(self):
        self.pinDat = self.config["pins"]["dat"]
        self.pinClk = self.config["pins"]["clk"]
        
        from devices.hx711v0_5_1 import HX711 # 2-wire interface: Clock, Data 
        self.hx = HX711(self.pinDat, self.pinClk)
        self.hx.setReadingFormat("MSB", "MSB")
        self.hx.autosetOffset()
        self.hx.setReferenceUnit(3000)

    # return the current value of the sensor
    def sample(self):
        dataList = self.hx.getWeight()
        return dataList

    def calibrate(self):
        if self.testMode == False:
            self.hx.autosetOffset() # Tare function
            logging.info(f"{self.name}: tare")
        else:
            logging.info(f"{self.name}: tare. TESTMODE. NO DATA WAS SEND TO DEVICE!")

    # fitting random value generation
    def randomValues(self):
        dataList = round(random()*100,1)
        return dataList



class Environment(Sensor):
    def __init__(self, name, config):
        super().__init__(name, config)
        
    def updateData(self):
        """dict that saves current data points of motor as well as names and units."""
        if self.testMode == False: self.data = [{"name": "Roomtemp", "val" : self.sample()[0]      , "unit": "deg",}, {"name": "Humidity", "val" : self.sample()[1]      , "unit": "%",}]
        else:                      self.data = [{"name": "Roomtemp", "val" : self.randomValues()[0], "unit": "deg",}, {"name": "Humidity", "val" : self.randomValues()[1], "unit": "%",}]

    # function to init the sensor
    def initSensor(self):
        import adafruit_sht31d # 2-wire I2C
        self.i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
        self.sht = adafruit_sht31d.SHT31D(self.i2c, 68) # default address = 0x44
        self.sht.mode = adafruit_sht31d.MODE_SINGLE
        self.sht.repeatability = adafruit_sht31d.REP_HIGH

    # return the current value of the sensor
    def sample(self):
        
        try:
            temperature = self.sht.temperature
        except Exception as e:
            temperature = 0
            logging.error(f"Unable to sample Temperature of SHT31 \n{e}\n")
        
        try:
            humidity = self.sht.relative_humidity
        except Exception as e:
            humidity = 0
            logging.error(f"Unable to sample Humidity of SHT31 \n{e}\n")
            
        return [temperature, humidity]

    # fitting random value generation
    def randomValues(self):
        dataList = [round(24+random()*10,1), round(24+random()*100)]
        return dataList



class Power(Sensor):
    def __init__(self, name, config):
        super().__init__(name, config)
        
    def updateData(self):
        """dict that saves current data points of motor as well as names and units."""
        if self.testMode == False: self.data = [{"name": "Current", "val" : self.sample()      , "unit": "mA",}]
        else:                      self.data = [{"name": "Current", "val" : self.randomValues(), "unit": "mA",}]

    # function to init the sensor
    def initSensor(self):
        import adafruit_ina219 # 2-wire I2C
        self.i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
        self.ina = adafruit_ina219.INA219(self.i2c) # default address = 0x40
        logging.debug("INA219 addr detected on I2C")
        # optional : change configuration to use 32 samples averaging for both bus voltage and shunt voltage
        self.ina.bus_adc_resolution = adafruit_ina219.ADCResolution.ADCRES_12BIT_32S
        self.ina.shunt_adc_resolution = adafruit_ina219.ADCResolution.ADCRES_12BIT_32S
        self.ina.bus_voltage_range = adafruit_ina219.BusVoltageRange.RANGE_16V

    # return the current value of the sensor
    def sample(self):
        dataList = self.ina.current
        return dataList

    # fitting random value generation
    def randomValues(self):
        dataList = 0
        return dataList
