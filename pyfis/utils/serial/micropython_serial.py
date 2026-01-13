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
    from machine import UART
    has_micropython = True
except ImportError:
    has_micropython = False

from .base_serial import BaseSerialPort


class MicropythonSerialPort(BaseSerialPort):
    def __init__(self, port, baudrate, **kwargs):
        if not has_micropython:
            raise RuntimeError("The MicroPython 'machine.UART' library was not found. It is needed to create MicropythonSerialPort objects.")
        self.baudrate = baudrate
        self.device_kwargs = kwargs
        self.device = UART(port)
        self.open()
    
    def open(self):
        self.device.init(self.baudrate, **self.device_kwargs)
    
    def close(self):
        self.device.deinit()

    def write(self, data):
        return self.device.write(data)

    def read(self, length):
        return self.device.read(length)
