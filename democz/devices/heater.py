# -*- coding: utf-8 -*-
"""Controles the Hotplate

controlles the hotplate based on input from control.py with the calclualtions from pid.py.
The duty cycles are very short so precice timings and a spereate thread are used.

Code is based from Dr. Kaspars Dadzis and was modified to fit an object oriented structure.
"""

import time
import logging
from threading import Thread

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except Exception as e:
    logging.warning(f"missing imports: {e}")

class Heater():
    def __init__(self, config):
        self.stopThreads = False
        self.config = config
        self.testMode = self.config["heater"]["skip"]
        self.kwh_val = 0
        
        if self.testMode == False:
            import RPi.GPIO as GPIO # for heating
        
        self.init_heating()
        
        thread_heating = Thread(target=self.update_heating_thread)
        thread_heating.start()

    def updateData(self):
        self.data = [{"name": "Power",  "val" : self.kwh_val,  "unit": "kwh"}]

    def getData(self):
        return self.data

    def setStopThreads(self):
        self.stopThreads = True

    def setInput(self, newOut):
        self.pid_out = newOut

    def init_heating(self):
        """starts the device"""
        self.ssr_pin           = self.config["heater"]["SSR_PIN"]
        self.heater_sampletime = self.config["sampletimes"]["HEATER_SAMPLETIME"]
        self.heater_power      = self.config["heater"]["HEATER_POWER"]
        self.pid_periode       = self.config["pid"]["PID_OUT_PERIOD"]
        self.pid_out_min       = self.config["pid"]["PID_OUT_MIN"]
        self.pid_out_max       = self.config["pid"]["PID_OUT_MAX"]
        self.pid_out           = self.pid_out_min
        self.lasttime_heat     = time.time_ns()

        if self.testMode == False:
            GPIO.setup(self.ssr_pin, GPIO.OUT)
            GPIO.output(self.ssr_pin, GPIO.LOW)
        
        self.updateData()
    
    def update_heating(self):
        """controls the dutycycle"""
        now = time.time_ns()
        if now - self.lasttime_heat > self.pid_periode  * 1000000 : 
            self.lasttime_heat = self.lasttime_heat + self.pid_periode  * 1000000
            if self.pid_out > self.pid_out_min : 
                self.kwh_val += self.pid_out/1000/3600 * self.heater_power # Calculate consumed energy as time[h] * power[kW]
                self.updateData()
    
        if self.pid_out > self.pid_out_min and self.pid_out * 1000000 > now - self.lasttime_heat :
            if self.testMode == False: GPIO.output(self.ssr_pin, GPIO.HIGH)
            else: pass
        else:
            if self.testMode == False:GPIO.output(self.ssr_pin, GPIO.LOW)
            else: pass

    def update_heating_thread(self) :
        """controls the Thread"""
        logging.info("started Heating thread")

        while self.stopThreads == False :
            self.update_heating()
            time.sleep(self.heater_sampletime/1000) 
        if self.testMode == False:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.ssr_pin, GPIO.OUT)
            GPIO.output(self.ssr_pin, GPIO.LOW)
        logging.info("finished Heating thread")
