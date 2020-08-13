"""
Copyright (C) 2020 Julian Metzler

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


class OmegaRS485Controller:
    """
    Controls split-flap modules using Omega's RS485 protocol.
    Commonly found in Swiss (SBB CFF FFS) station displays.
    """

    def __init__(self, port, debug = False):
        self.debug = debug
        self.port = serial.Serial(port, baudrate=19200, timeout=1.0)

    def prepare_message(self, address, command, value):
        message = [0xFF, command, address]
        if value is not None:
            message.append(value)
        return message

    def init_communication(self):
        """
        Initialize communication by asserting a break condition
        on the serial Tx line for a certain time
        """
        self.port.break_condition = True
        time.sleep(0.05)
        self.port.break_condition = False

    def send_raw_message(self, message):
        self.init_communication()
        self.port.write(message)

    def read_response(self, length):
        return self.port.read(length)

    def send_command(self, address, command, value = None):
        message = self.prepare_message(address, command, value)
        self.send_raw_message(message)

    def set_home(self, address):
        self.send_command(address, 0xC5)

    def set_position(self, address, position):
        self.send_command(address, 0xC0, position)

    def set_address(self, address, new_address):
        self.send_command(address, 0xCE, new_address)

    def read_position(self, address):
        self.send_command(address, 0xD0)
        return self.read_response(4)

    def read_serial_number(self, address):
        self.send_command(address, 0xDF)
        return self.read_response(1)

    def d_set_module_data(self, module_data):
        # Compatibility function for SplitFlapDisplay class
        for addr, pos in module_data:
            self.set_position(addr, pos)

    def d_update(self):
        # Compatibility function for SplitFlapDisplay class
        pass
