"""
Copyright (C) 2026 Julian Metzler

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

try:
    import serial
    has_serial = True
except ImportError:
    has_serial = False

from .base_serial import BaseSerialPort


class SerialPort(BaseSerialPort):
    def __init__(self, *args, **kwargs):
        if not has_serial:
            raise RuntimeError("The serial library was not found. It is needed to create SerialPort objects.")
        self.device = serial.Serial(*args, **kwargs)

    def __setattr__(self, name, val):
        if name == "break_condition":
            self.device.break_condition = val
        else:
            super().__setattr__(name, val)
    
    def open(self):
        return self.device.open()
    
    def close(self):
        return self.device.close()

    def write(self, data):
        return self.device.write(data)

    def read(self, length):
        return self.device.read(length)

    def inWaiting(self):
        return self.device.inWaiting()

    def setRTS(self, state):
        self.device.rts = state

    def setDTR(self, state):
        self.device.dtr = state

    def getCTS(self):
        return self.device.cts

    def getDSR(self):
        return self.device.dsr

    def getRI(self):
        return self.device.ri

    def getCD(self):
        return self.device.cd
