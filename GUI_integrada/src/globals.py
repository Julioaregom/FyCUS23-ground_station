'''
# Author/s: Julio Arévalo Gómez, Gonzalo Arévalo Gómez
# Email: julioaregom02@gmail.com , gonzalo.arevalo.gomez@gmail.com
# Project: FyCUS23 / 2023 Edition
# License: GNU General Public License, version 3 (GPL-3.0)
'''

"""
Global Configuration Module

This file contains DEFAULT global configuration variables.
These can be changed with the menu-bar of the UI.
"""

# Serial port name and baud rate
SERIAL_PORT = "COM7"
BAUD_RATE = 9600

# Data send frequency when tracking mode (seconds)
TR_SEND_FREQ = 1

# Settle point reference coordinates (Sevilla)
REF_LAT = 37.411644  # Reference latitude
REF_LON = -6.000173 # Reference longitude
REF_ALT = 7.0  # Reference altitude

GLOBAL_GNSS=[]