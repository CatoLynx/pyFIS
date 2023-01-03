"""
Copyright 2019 - 2023 Julian Metzler

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

import serial
import time

from .exceptions import CommunicationError
from ..utils.base_serial import BaseSerialPort


class Krone8200PST:
    """
    Controls the PST bus in a Krone 8200 split-flap display.
    """

    def __init__(self, port, debug = False, exclusive = True):
        self.debug = debug
        if isinstance(port, serial.Serial) or isinstance(port, BaseSerialPort):
            self.port = port
        else:
            self.port = serial.Serial(port, baudrate=2400, timeout=1.0, exclusive=exclusive)

    def debug_message(self, message):
        """
        Turn a message into a readable form
        """
        result = ""
        for byte in message:
            result += "{:02X} ".format(byte)
        return result

    def send_raw_message(self, message):
        if self.debug:
            print("TX: " + self.debug_message(message))
        for byte in message:
            self.port.write(bytearray([byte]))
            time.sleep(0.05)

    def set_home(self):
        """
        Set all units to their home position
        """
        return self.send_raw_message([0x1B])

    def set_unit(self, address, position):
        """
        Set a given unit to a given position
        """
        return self.send_raw_message([0x3A, address, position])

    def update(self):
        """
        Update units (cause them to actually turn)
        """
        return self.send_raw_message([0x1C])

    def reset(self):
        """
        Reset all unit controllers
        """
        return self.send_raw_message([0x1A])

    def d_set_module_data(self, module_data):
        # Compatibility function for SplitFlapDisplay class
        for addr, pos in module_data:
            self.set_unit(addr, pos)

    def d_update(self):
        # Compatibility function for SplitFlapDisplay class
        self.update()
