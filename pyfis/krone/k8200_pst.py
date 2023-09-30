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
from ..utils.utils import int_to_bcd


class Krone8200PST:
    """
    Controls the PST bus in a Krone 8200 split-flap display.
    """

    def __init__(self, port, nmi_backend, nmi_channel, nmi_invert, debug = False, exclusive = True):
        """
        nmi_backend: GPIO Backend instance to control the NMI pin of the PST.
                     This pin is used to stop a module from spinning in case
                     the selected position can not be found.
                     See the supported backends in pyfis.gpio_backends.
        nmi_channel: Channel to use for the NMI signal on the selected GPIO backend
        nmi_invert:  Whether the NMI signal is active-low (False) or active-high (True)
        """

        self.nmi_backend = nmi_backend
        self.nmi_channel = nmi_channel
        self.nmi_invert = nmi_invert
        self.nmi_backend.setup_channel(self.nmi_channel, self.nmi_backend.MODE_OUT)
        self.nmi_backend.set_output(self.nmi_channel, self.nmi_backend.STATE_LOW if self.nmi_invert else self.nmi_backend.STATE_HIGH)
        self.debug = debug
        if isinstance(port, serial.Serial) or isinstance(port, BaseSerialPort):
            self.port = port
        else:
            self.port = serial.Serial(port, baudrate=2400, stopbits=2, timeout=1.0, exclusive=exclusive)

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
        return self.send_raw_message([0x3A, address, int_to_bcd(position)])

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

    def stop_all(self):
        """
        Stop all modules from rotating by asserting NMI
        """
        self.nmi_backend.set_output(self.nmi_channel, self.nmi_backend.STATE_HIGH if self.nmi_invert else self.nmi_backend.STATE_LOW)
        time.sleep(0.05)
        self.nmi_backend.set_output(self.nmi_channel, self.nmi_backend.STATE_LOW if self.nmi_invert else self.nmi_backend.STATE_HIGH)
        time.sleep(0.05)

    def d_set_module_data(self, module_data):
        # Compatibility function for SplitFlapDisplay class
        for addr, pos in module_data:
            self.set_unit(addr, pos)

    def d_update(self):
        # Compatibility function for SplitFlapDisplay class
        self.update()
