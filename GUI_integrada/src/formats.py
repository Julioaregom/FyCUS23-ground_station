#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  3 19:47:49 2023
@author: Carlos Martinez Mora
@email: carmamo.95@gmail.com
"""

LTC4162_RSNSI = 0.010
LTC4162_RSNSB = 0.010
LTC4162_RNTCBIAS = 10000.0
LTC4162_RNTCSER = 0.0
LTC4162_VINDIV = 30.0
LTC4162_VOUTDIV = (30.0 * 1.00232)
LTC4162_BATDIV = 3.5
LTC4162_AVPROG = 37.5
LTC4162_AVCLPROG = 37.5
LTC4162_ADCGAIN = 18191.0
LTC4162_VREF = 1.2
LTC4162_Rm40 = 214063.67
LTC4162_Rm34 = 152840.30
LTC4162_Rm28 = 110480.73
LTC4162_Rm21 = 76798.02
LTC4162_Rm14 = 54214.99
LTC4162_Rm6 = 37075.65
LTC4162_R4 = 23649.71
LTC4162_R33 = 7400.97
LTC4162_R44 = 5001.22
LTC4162_R53 = 3693.55
LTC4162_R62 = 2768.21
LTC4162_R70 = 2167.17
LTC4162_R78 = 1714.08
LTC4162_R86 = 1368.87
LTC4162_R94 = 1103.18
LTC4162_R102 = 896.73
LTC4162_R110 = 734.86
LTC4162_R118 = 606.86
LTC4162_R126 = 504.80
LTC4162_R134 = 422.81
LTC4162_R142 = 356.45
LTC4162_R150 = 302.36

def __LTC4162_RLINE__(x0,x1,y0,y1,x):
    return ((y0) + ((y1) - (y0))/((x1) - (x0)) * ((x) - (x0)))
def LTC4162_VBAT_FORMAT_I2R(y):
    cell_count=2
    return (__LTC4162_RLINE__((0), (1), (0), (LTC4162_BATDIV / LTC4162_ADCGAIN), (y)))*cell_count

def LTC4162_IBAT_FORMAT_I2R(y):
    
    return __LTC4162_RLINE__((0), (1), (0), (1 / LTC4162_RSNSB / LTC4162_AVPROG / LTC4162_ADCGAIN), (y))

def LTC4162_VOUT_FORMAT_I2R(y):
    
    return __LTC4162_RLINE__((0), (1), (0), (LTC4162_VOUTDIV / LTC4162_ADCGAIN), (y))

def LTC4162_VIN_FORMAT_I2R(y):
    
    return __LTC4162_RLINE__((0), (1), (0), (LTC4162_VINDIV / LTC4162_ADCGAIN), (y))

def LTC4162_IIN_FORMAT_I2R(y):
    
    return __LTC4162_RLINE__((0), (1), (0), (1 / LTC4162_RSNSI / LTC4162_AVCLPROG / LTC4162_ADCGAIN), (y))

def LTC4162_DIE_TEMP_FORMAT_I2R(y):
    
    return __LTC4162_RLINE__((0), (1), (-264.4), (-264.4 + 1 / 46.557), (y))

def LTC4162_CHARGER_STATE(y):
    
    states = {
        0: "Error",
        1: "Shorted Battery",
        2: "Open Battery",
        4: "Max Time Fault",
        8: "C/X Termination",
        16: "Timer Termination",
        32: "NTC Pause",
        64: "CC/CV Charge",
        128: "Precharge",
        256: "Suspended",
        2048: "Bat Detection",
        4096: "Bat Detect Failed"
    }
    
    charger_state = states.get(y, "")
    
    return charger_state
    

def format_telemetry(packet):
    
    
    return

    