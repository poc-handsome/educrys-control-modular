# -*- coding: utf-8 -*-
"""Control of DemoCz

This Object will recive inputs from internal or external view instances and will controll the devices. This is the "brain" of the program.

Code is based from Dr. Kaspars Dadzis and was modified to fit an object oriented structure.
"""

import logging
import time
from threading import Thread
import yaml

class Control():
    def __init__(self):

        logging.info("Start of Controller")

        # Read Config
        # source: https://stackoverflow.com/questions/1773805/how-can-i-parse-a-yaml-file-in-python
        with open("config.yml") as stream: 
            try:
                self.config = yaml.safe_load(stream)
                logging.info(self.config)
            except yaml.YAMLError as exc:
                logging.error(exc)

        self.deviceSampletime      = self.config["sampletimes"]["DEVICE_SAMPLETIME"]
        self.dataStorageSampletime = self.config["sampletimes"]["DATA_SAMPLETIME"]
        self.completeTempList      = []
        
        # Variables
        self.time_start  = time.time_ns()
        self.stopThreads = False
        self.lock        = False

        # imports
        from devices.camera import CameraList
        from devices.device import DeviceList
        from devices.motor  import MotorList
        from devices.sensor import SensorList
        from devices.heater import Heater
        from devices.pid    import Pid

        # PID
        self.pid     = Pid(self.config)
        self.pidDict = self.pid.getData()

        # Heater
        self.heater = Heater(self.config)
        self.heaterDict = self.heater.getData()

        #Camera
        self.cameraDict = CameraList(self.config).getCameraDict()

        # Motor
        self.motorDict, self.motorDataDict = MotorList(self.config).getData()
        self.linMotor                 = self.motorDict.get("linMotor")

        #Sensor
        sensors             = SensorList(self.config)
        self.sensorList     = sensors.getSensorList()
        self.weightSensor   = sensors.getWeightSensor()
        self.sensorDict     = {}

        # Other Devices
        devices     = DeviceList(self.config)
        self.buzzer = devices.getBuzzer()
        self.led    = devices.getLed()

        # Internal Threads
        threadDataStorage = Thread(target=self.updateDataStorageThread)
        threadDevices     = Thread(target=self.updateDevicesThread)
        threadDataStorage.start()
        
        # CMD-Thread
        if self.config["userInterfaces"]["cmd"] == True:
            logging.info("CMD Thread enabled by Config")
            import view
            self.v = view.View()
            self.v.start(self.config)
            self.v.setSpeedDataDict(self.motorDataDict)

        # External GUI Thread
        if self.config["userInterfaces"]["gui"] == "localhost":
            logging.info("GUI Thread enabled by Config")
            from interfaceDemocz import InterfaceDemocz
            self.link = InterfaceDemocz(self.config)

        
        self.initDataStorage()
        threadDevices.start()

        time.sleep(1) # Wait one second to let everything start
        logging.info("All Threads started and ready")

        # Check if Program should End
        while self.stopThreads == False:
            # Program gets "stuck" here intentionally, work is distributed on threads
            self.checkClosing()
            time.sleep(0.5)

### Functions: #################################################
    def updateDevices(self):
        """This function checks if an input was made. If detected, the device will execute the action via a callable function."""

        """
        # TODO Healthcheck 
        if not self.link.getTargetTemp():
            logging.critical("________________________\nConnection ti GUI Failed.\n________________________")
            self.config["userInterfaces"]["cmd"] = False # Setting GUI to false so DemoCZ can still run without errors
        """
    # Heating
        # Update Input heat for PID calculation
        oldInput = self.pid.getInputSensor()
        #if self.config["userInterfaces"]["gui"] != False: newInput = self.link.getInputSensor()
        if self.config["userInterfaces"]["cmd"] == True:  newInput = self.v.getInputSensor()
        else: newInput = oldInput

        self.pid.setInputSensor(newInput)
        if newInput == "PT1":
            try:
                self.pid.setInput(self.sensorDict["PT1"])
            except Exception as e:
                self.v.setInputSensor(oldInput)
                logging.error(f"Update of Input Temperature for PID Calcluation was not Possible. Input Device: 'PT1'\n{e}")
        elif newInput  == "TC1":
            try:
                self.pid.setInput(self.sensorDict["TC1"])
            except Exception as e:
                self.v.setInputSensor(oldInput)
                logging.error(f"Update of Input Temperature for PID Calcluation was not Possible. Input Device: 'TC1'\n{e}")
        elif newInput == "TC2":
            try:
                self.pid.setInput(self.sensorDict["TC2"]) 
            except Exception as e:
                self.v.setInputSensor(oldInput)
                logging.error(f"Update of Input Temperature for PID Calcluation was not Possible. Input Device: 'TC2'\n{e}")

        # Change Target Temperature for heating
        oldT = self.pidDict[0]["val"]
        if self.config["userInterfaces"]["cmd"] == True:  newT = self.v.getTargetTemp()
        elif self.config["userInterfaces"]["gui"] != False: newT = self.link.getTargetTemp()
        else: newT = oldT

        if oldT != newT: # if an input was made
            if newT >= self.pid.getPidMinMax()[0] and newT <= self.pid.getPidMinMax()[1]: # if the input was valid
                self.pid.setPidSet(newT)
                if self.config["userInterfaces"]["cmd"] == True: self.v.setTargetTemp(newT)
                elif self.config["userInterfaces"]["gui"] != False: self.link.setTargetTemp(newT)
                logging.info(f"Change of Target Temperature to {newT}.")
                time.sleep(2) # Timing issues # TODO find better solution
            else:
                if self.config["userInterfaces"]["cmd"] == True: self.v.setTargetTemp(oldT) # return view to old value if comand was not executed
                logging.warning(f"Change Target Temperature to {newT} not possible, above max or below min Value. minT:{self.Pid.getPidMinMax()[0]}, maxT:{self.Pid.getPidMinMax()[1]}")
        
        # Power Reset
        #if self.config["userInterfaces"]["cmd"] == True: powerReset = self.v.getPowerReset() #TODO: Implement in cmd
        if self.config["userInterfaces"]["gui"] != False: powerReset = self.link.getPowerReset()
        else: powerReset = False
        
        if powerReset == True:
            self.kwh = 0
            #if self.config["userInterfaces"]["cmd"] == True: powerReset = self.v.setPowerReset(False) #TODO: Implement in cmd
            if self.config["userInterfaces"]["gui"] != False: self.link.setPowerReset(False)
            logging.info("Reset power consumtion to 0 kwh.")
        
    # Motors
        # Change Linear Position
        oldPos = self.linMotor.getPos()
        if self.config["userInterfaces"]["cmd"] ==  True: newPos = self.v.getPos()
        elif self.config["userInterfaces"]["gui"] != False: newPos = self.link.getPos()
        else: newPos = oldPos

        if oldPos != newPos and self.linMotor.getSpeed() == 0:
            if newPos >= self.linMotor.posMin - 1 and newPos <= self.linMotor.posMax + 1:
                self.linMotor.setPos(newPos)
                if self.config["userInterfaces"]["cmd"] ==  True:
                    self.v.setPos(newPos)
                    newPos = self.v.getPos()
                elif self.config["userInterfaces"]["gui"] != False:
                    self.link.setPos(newPos)
                    newPos = self.link.getPos()
                oldPos = newPos
                logging.info(f"Change of linPos to {newPos}.")
            else:
                if self.config["userInterfaces"]["cmd"] == True: self.v.setPos(oldPos)
                if self.config["userInterfaces"]["gui"] != False: self.link.setPos(oldPos)
                logging.warning(f"Change of Position to {newPos} not possible, above max or below min Value. minPos:{self.linMotor.posMin}, maxPos:{self.linMotor.posMax}")
        
        if oldPos >= self.linMotor.getMinMax()[0] and oldPos <= self.linMotor.getMinMax()[1]:
            pass
        elif self.linMotor.getSpeed() != 0:
            logging.warning("Maximum Position reached. Stopping Linear Motion!")
            self.linMotor.setSpeed(0)      # Stop Motor
            if self.config["userInterfaces"]["cmd"] ==  True: self.v.setSpeed("linMotor", 0) # change displayed Data
            if self.config["userInterfaces"]["gui"] != False: self.link.setLinSpeed(0)

            self.linMotor.setPos( round(oldPos) ) # Reset Position to a Save Value
            if self.config["userInterfaces"]["cmd"] ==  True: self.v.setPos(   round(oldPos)) # change displayed Data
            if self.config["userInterfaces"]["gui"] != False: self.link.setPos(round(oldPos))

        # Change Motor Speed
        for motor in self.motorDict:
            tempName     = self.motorDict.get(motor).getName()
            tempSpeedOld = self.motorDict.get(motor).getSpeed()

            if self.config["userInterfaces"]["cmd"] ==  True: tempSpeedNew = self.v.getSpeed(tempName)
            elif self.config["userInterfaces"]["gui"] != False: 
                if   tempName == "linMotor": tempSpeedNew = self.link.getLinSpeed()
                elif tempName == "rotMotor": tempSpeedNew = self.link.getRotSpeed()
                elif tempName == "fan": tempSpeedNew = self.link.getFanSpeed()
            else: tempSpeedNew = tempSpeedOld
            if tempSpeedOld != tempSpeedNew and tempSpeedNew != None: # if an input was made
                logging.info(f"{tempName}: changing Speed to {tempSpeedNew}")
                returnVal = self.motorDict.get(motor).setSpeed(tempSpeedNew)
                self.linMotor.setPos(oldPos)
                if self.config["userInterfaces"]["cmd"] ==  True: self.v.setPos(oldPos)
                elif self.config["userInterfaces"]["gui"] != False: 
                    if   tempName == "linMotor": self.link.setLinSpeed(tempSpeedNew)
                    elif tempName == "rotMotor": self.link.setRotSpeed(tempSpeedNew)
                    elif tempName == "fan": self.link.setFanSpeed(tempSpeedNew)
                if returnVal == -1: # return view to old value if comand was not executed
                    logging.warning("returning to old value,  Change was not accepted.")
                    if self.config["userInterfaces"]["cmd"] == True: self.v.setSpeed(tempName, tempSpeedOld)

    # Weight
        # Tare function
        if self.config["userInterfaces"]["cmd"] ==  True: getTare = self.v.getTare()
        elif self.config["userInterfaces"]["gui"] != False: getTare = self.link.getTare()
        else: getTare = False

        if getTare == True:
            self.weightSensor.calibrate()
            if self.config["userInterfaces"]["cmd"] ==  True: self.v.setTare(False)
            elif self.config["userInterfaces"]["gui"] != False: self.link.setTare(False)

    # Cameras
        for cam in self.cameraDict:
            if cam == "cam":

                if self.config["userInterfaces"]["cmd"] ==  True: getTakePicVis = self.v.getTakePicVis()
                elif self.config["userInterfaces"]["gui"] != False: getTakePicVis = self.link.getTakePicVis()
                else: getTakePicVis = False

                if getTakePicVis == True:
                    self.cameraDict.get(cam).getPicture()
                    if self.config["userInterfaces"]["cmd"] ==  True: self.v.setTakePicVis(False)
                    elif self.config["userInterfaces"]["gui"] != False:
                        #self.link.sendVisPic(pic)
                        self.link.setTakePicVis(False)

            elif cam == "irCam":
                if self.config["userInterfaces"]["cmd"] == True:  getTakePicIr = self.v.getTakePicIr()
                elif self.config["userInterfaces"]["gui"] != False: getTakePicIr = self.link.getTakePicIr()
                else: getTakePicIr = False

                if getTakePicIr == True:
                    self.cameraDict.get(cam).getPicture()
                    if self.config["userInterfaces"]["cmd"] ==  True: self.v.setTakePicIr(False)
                    elif self.config["userInterfaces"]["gui"] != False: self.link.setTakePicIr(False)
            # Add new Cameras here to implent pcting picture function

        # Exp
        try: oldExp = self.cameraDict["cam"].getExp()
        except: oldExp = 300000
        if self.config["userInterfaces"]["cmd"] ==  True:   newExp = self.v.getExp()
        elif self.config["userInterfaces"]["gui"] != False: newExp = self.link.getExp()
        else: newExp = oldExp
        
        if newExp != oldExp:
            self.cameraDict["cam"].setExp(newExp)
            if self.config["userInterfaces"]["cmd"] ==  True:   self.v.setExp(newExp)
            elif self.config["userInterfaces"]["gui"] != False: self.link.setExp(newExp)

    # LED
        if self.config["userInterfaces"]["cmd"] ==  True:   getToggleLED = self.v.getToggleLED()
        elif self.config["userInterfaces"]["gui"] != False: getToggleLED = self.link.getToggleLED()
        else: getToggleLED = False

        if getToggleLED == True:
            self.led.setOutput( not self.led.getState() )
            if self.config["userInterfaces"]["cmd"] ==  True:   self.v.setToggleLED(False)
            elif self.config["userInterfaces"]["gui"] != False: self.link.setToggleLED(False)

    # Buzzer
        if self.config["userInterfaces"]["cmd"] == True:    buzzerState = self.v.getToggleBuzzer()
        elif self.config["userInterfaces"]["gui"] != False: buzzerState = self.link.getToggleBuzzer()
        else: buzzerState = False

        if buzzerState == True:
            self.buzzer.setState(not self.buzzer.getState() )
            if self.config["userInterfaces"]["cmd"] == True:    self.v.setToggleBuzzer(False)
            elif self.config["userInterfaces"]["gui"] != False: self.link.setToggleBuzzer(False)
        
        oldAlarmIn = self.buzzer.getAlarmIn()
        if self.config["userInterfaces"]["cmd"] == True:    newAlarmIn = self.v.getAlarmIn()
        elif self.config["userInterfaces"]["gui"] != False: newAlarmIn = self.link.getAlarmIn()
        else: newAlarmIn = oldAlarmIn

        if newAlarmIn != oldAlarmIn:
            if newAlarmIn > 0 and self.lock == False:
                self.buzzer.setAlarmIn(newAlarmIn)
                if self.config["userInterfaces"]["cmd"] == True:    self.v.setAlarmIn(newAlarmIn)
                elif self.config["userInterfaces"]["gui"] != False: self.link.setAlarmIn(newAlarmIn)
                self.lock = True
            elif newAlarmIn > 0 and self.lock == True:
                if self.config["userInterfaces"]["cmd"] == True:    self.v.setAlarmIn(round(oldAlarmIn,1))
                elif self.config["userInterfaces"]["gui"] != False: self.link.setAlarmIn(round(oldAlarmIn,1))
                self.alarmTime = round(oldAlarmIn,1)
            if newAlarmIn < 0:
                self.buzzer.setState(True)
                if self.config["userInterfaces"]["cmd"] == True:    self.v.setAlarmIn(0)
                elif self.config["userInterfaces"]["gui"] != False: self.link.setAlarmIn(0)
                self.buzzer.setAlarmIn(0)
                self.lock = False
        
        if self.config["userInterfaces"]["cmd"] == True: self.v.updateGui(self.motorDataDict, self.completeTempList) # Send Data to CMD-Gui
        


    def updateDevicesThread(self):
        """Executes the self.updateDevices() function periodicly and stops it if needed."""

        logging.info("starting Device Thread")
        while self.stopThreads == False:
            self.updateDevices()
            time.sleep(self.deviceSampletime/1000)
        logging.info("finished Device Thread")       



    def initDataStorage(self):
        """Prepares an output file with all relevent data.

        Will not save any Data.
        
        """
        fname = time.strftime("%Y%m%d-%H%M%S")
        self.fdatanamestr = "./data/datafile_{:s}.csv".format(fname)
        
        dataStr = "time"
        for sensor in self.sensorList:
            newData = sensor.read()
            for entry in newData:
                dataStr += f', {entry["name"]} [{entry["unit"]}]'


        for motor in self.motorDict:
            tempMotor = self.motorDict.get(motor)
            tempMotor = tempMotor.read()
            for entry in tempMotor:
                dataStr += f', {entry["name"]} [{entry["unit"]}]'


        for pidData in self.pidDict:
            dataStr += f', {pidData["name"]} [{pidData["unit"]}]'
        
        for heaterData in self.heaterDict:
            dataStr += f', {heaterData["name"]} [{heaterData["unit"]}]'

        dataStr += "\n"

        with open(self.fdatanamestr, "a") as fileDAT:
            fileDAT.write(dataStr)



    def updateDataStorage(self):
        """Gets newest Data from devices contiously, saves them continously, and distribute the data to displaying objects"""
        
        # init data 
        self.pt1      = 0
        self.tc1      = 0
        self.tc2      = 0
        self.env      = 0
        self.hum      = 0
        self.weight   = 0
        self.kwh      = 0
        self.current  = 0
        self.linSpeed = 0
        self.rotSpeed = 0
        self.fanSpeed = 0
        self.pos      = 0
        self.pidOut   = 0
        self.pidSet   = 0
        self.alarmTime= 0
        
        now = time.time_ns()
        tt = (now - self.time_start)/1000000000
        serdata = [tt]
        
        # Update Data
        self.heater.setInput(self.pid.getOutput()) # Update PID Calculation to heater
        
        try:
            self.link.setVisFilename(self.cameraDict.get(  "cam").getFileName())
            self.link.setIrFilename( self.cameraDict.get("irCam").getFileName())
        except:
            pass
        
        self.pidDict    = self.pid.getData()
        self.heaterDict = self.heater.getData()

        newTempList = []

        for sensor in self.sensorList:
            newData = sensor.read()
            for entry in newData:
                self.sensorDict.update({entry["name"] : entry["val"] })
                serdata.append(entry["val"])
                newTempList.append([entry["name"], entry["val"], entry["unit"]])
                if self.config["userInterfaces"]["gui"] != False:
                    if   entry["name"] == "PT1":      self.pt1     = entry["val"]
                    elif entry["name"] == "TC1":      self.tc1     = entry["val"]
                    elif entry["name"] == "TC2":      self.tc2     = entry["val"]
                    elif entry["name"] == "Roomtemp": self.env     = entry["val"]
                    elif entry["name"] == "Humidity": self.hum     = entry["val"]
                    elif entry["name"] == "Weight":   self.weight  = entry["val"]
                    elif entry["name"] == "Current":  self.current = entry["val"]
        
        for motor in self.motorDict:
            newData = self.motorDict.get(motor).read()
            for entry in newData:
                serdata.append(entry["val"])
                newTempList.append([entry["name"], entry["val"], entry["unit"]])
                if self.config["userInterfaces"]["gui"] != False:
                    if   entry["name"] == "LinSpeed": self.linSpeed = entry["val"]
                    elif entry["name"] == "RotSpeed": self.rotSpeed = entry["val"]
                    elif entry["name"] == "FanSpeed": self.fanSpeed = entry["val"]
                    elif entry["name"] == "LinPos"  : self.pos      = entry["val"]

        for entry in self.pidDict:
            serdata.append(entry["val"])
            newTempList.append([entry["name"], entry["val"], entry["unit"]])
            if self.config["userInterfaces"]["gui"] != False:
                    if   entry["name"] == "pid_set": self.pidSet = entry["val"]
                    elif entry["name"] == "pid_out": self.pidOut = entry["val"]

        
        for entry in self.heaterDict:
            serdata.append(entry["val"])
            newTempList.append([entry["name"], entry["val"], entry["unit"]])
            if self.config["userInterfaces"]["gui"] != False:
                if   entry["name"] == "Power": self.kwh= entry["val"]

        self.completeTempList = newTempList

        try:
            with open(self.fdatanamestr, "a") as fileDAT:
                    for i in serdata:
                        fileDAT.write(str(i))
                        fileDAT.write(', ')
                    fileDAT.write('\n')
        except:
            pass

        self.guiData = {
            "tt"      : tt,
            "pt1"     : self.pt1,            # Sensors
            "tc1"     : self.tc1,
            "tc2"     : self.tc2,
            "env"     : self.env,
            "hum"     : self.hum,
            "weight"  : self.weight,
            "kwh"     : self.kwh,
            "current" : self.current,
            "linSpeed": self.linSpeed,       # Motors
            "rotSpeed": self.rotSpeed,
            "fanSpeed": self.fanSpeed,
            "linPos"  : self.pos,
            "PidOut"  : self.pidOut,         # PID
            "PidSet"  : self.pidSet,
            "alarmIn" : self.alarmTime
        }

        try:
            self.link.setGuiData(self.guiData)
        except Exception as e:
            pass
            #logging.error(f"sending Data to GUI failed:\n{self.guiData}\n{e}")


    # handels Data Storage Thread
    def updateDataStorageThread(self):
        """Executes the self.updateDataStorage() function periodicly and stops it if needed."""

        logging.info("starting Data Storage Thread")
        while self.stopThreads == False:
            self.updateDataStorage()
            time.sleep(self.dataStorageSampletime/1000)
        logging.info("finished Data Storage Thread ")


    def checkClosing(self):
        """checks if closing should occure and excutes it"""

        if   self.config["userInterfaces"]["cmd"]  == True: closing = self.v.getClosingEvent()
        elif self.config["userInterfaces"]["gui"] != False: closing = self.link.getClosingEvent()
        
        if closing == True:
                logging.info("Closing Threads")
                try: self.link.close()
                except: pass
                self.linMotor.setStopThreads()
                self.heater.setStopThreads()
                self.pid.setStopThreads()
                for entry in self.cameraDict: self.cameraDict.get(entry).setStopThreads()
                self.buzzer.setStopThreads()

                self.stopThreads = True
                #GPIO.cleanup()
                time.sleep(1)
                exit()
