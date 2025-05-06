# -*- coding: utf-8 -*-
"""Controles the PID-Calculations

A clasic pid calculation is used to detemin if the SSR relay should be swiched on or off. The swiching itself is happening in the heater.py file.

Code is based from Dr. Kaspars Dadzis and was modified to fit an object oriented structure.
"""

import time
import logging
from threading import Thread

class Pid():
    def __init__(self, config):
        self.config = config
        self.stopThreads = False
        self.data = []
        self.init_pid()

        thread_pid = Thread(target=self.update_pid_thread)
        thread_pid.start()

    def updateData(self):
        """gathers data to display"""
        self.data = [
            {"name": "pid_set",  "val" : self.pid_set,  "unit": "deg"},
            {"name": "pid_in",   "val" : self.pid_in,   "unit": "deg"},
            {"name": "pid_sel",  "val" : self.pid_sel,  "unit": ""   },
            {"name": "pid_mode", "val" : self.pid_mode, "unit": ""   },
            {"name": "pid_out",  "val" : self.pid_out,  "unit": ""   },
        ]

    def setStopThreads(self):
        self.stopThreads = True

    def getData(self):
        return self.data
        
    def setPidSet(self, newSet):
        self.pid_set = newSet
    
    def getInput(self):
        return self.input
    
    def setInput(self, newValue):
        self.input = newValue

    def getInputSensor(self):
        return self.pid_sel

    def setInputSensor(self, newInput):
        self.pid_sel = newInput

    def getPidMinMax(self):
        return [self.pid_set_min, self.pid_set_max]

    def getOutput(self):
        return self.pid_out

    def init_pid(self) :
        """starts the pid calculation"""
        self.pid_sampletime = self.config["sampletimes"]["HEATER_SAMPLETIME"]
        self.pid_out_min    = self.config["pid"]["PID_OUT_MIN"]
        self.pid_out_max    = self.config["pid"]["PID_OUT_MAX"]
        self.pid_periode    = self.config["pid"]["PID_OUT_PERIOD"]
        self.pid_kp         = self.config["pid"]["PID_KP"]
        self.pid_ki         = self.config["pid"]["PID_KI"]
        self.pid_kd         = self.config["pid"]["PID_KD"]
        self.pid_set_min    = self.config["pid"]["PID_SET_MIN"]
        self.pid_set_max    = self.config["pid"]["PID_SET_MAX"]
        
        pid_sampletime_s    = self.pid_sampletime / 1000
        self.pid_kp_norm    = self.pid_kp
        self.pid_ki_norm    = self.pid_ki * pid_sampletime_s 
        self.pid_kd_norm    = self.pid_kd / pid_sampletime_s

        self.pid_in       = 0 # self.sensorDataDict["PT1"]
        self.pid_in_old   = 0 # self.sensorDataDict["PT1"]
        self.pid_out      = self.pid_out_min
        self.pid_out_i    = self.pid_out
        self.lasttime_pid = 0
        self.pid_mode     = 1
        self.pid_out_man  = self.pid_out_min
        self.pid_set      = 0
        self.pid_sel      = "PT1"
        self.input        = 22 # avarage room Temp as start Value

        self.updateData()

    def update_pid(self) :
        """executes the pid calculation"""
        now = time.time_ns()
    
        if now - self.lasttime_pid > self.pid_sampletime * 1000000 and self.pid_mode == 1 :
            # INPUT: selection which sensors is responsible for PID calc
            self.pid_in = self.input
        
            pid_out_p = self.pid_kp_norm*(self.pid_set - self.pid_in)
        
            self.pid_out_i = self.pid_out_i + self.pid_ki_norm*(self.pid_set - self.pid_in)
            if self.pid_out_i > self.pid_out_max : 
                self.pid_out_i = self.pid_out_max
            elif self.pid_out_i < self.pid_out_min : 
                self.pid_out_i = self.pid_out_min 
        
            pid_out_d = -self.pid_kd_norm*(self.pid_in - self.pid_in_old)

            self.pid_out = pid_out_p + self.pid_out_i + pid_out_d # OUTPUT: used for heating thread

            if self.pid_out > self.pid_out_max : 
                self.pid_out = self.pid_out_max
            elif self.pid_out < self.pid_out_min : 
                self.pid_out = self.pid_out_min         
        
            self.lasttime_pid = now
            self.pid_in_old = self.pid_in
        
        if self.pid_mode == 0 :
            self.pid_out = self.pid_out_man

        self.updateData()

    def update_pid_thread(self):
        """controls the Thread"""
        logging.info("started PID thread")
        while self.stopThreads == False :
            self.update_pid()
            time.sleep(self.pid_sampletime/1000)
        logging.info("finished PID thread")