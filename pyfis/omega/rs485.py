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

    def __init__(self, port, debug = False, exclusive = False):
        self.debug = debug
        if isinstance(port, serial.Serial):
            self.port = port
        else:
            self.port = serial.Serial(port, baudrate=19200, timeout=1.0, exclusive=exclusive)

    def prepare_message(self, address, command, value):
        message = [0xFF, command, address]
        if value is not None:
            if type(value) in (tuple, list):
                message.extend(value)
            else:
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
        if self.debug:
            print(" ".join((format(x, "02X") for x in message)))
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
        
        # Turn module data into blocks of contiguous addresses
        items = sorted(module_data, key=lambda i:i[0])
        last_addr = None
        start_addr = None
        pos_block = []
        for i, (addr, pos) in enumerate(items):
            if (last_addr is not None and addr - last_addr > 1):
                self.set_position(start_addr, pos_block)
                time.sleep(0.05)
                pos_block = []
            if pos_block == []:
                start_addr = addr
            pos_block.append(pos)
            if i == len(items) - 1:
                self.set_position(start_addr, pos_block)
                time.sleep(0.05)
                pos_block = []
            last_addr = addr

    def d_update(self):
        # Compatibility function for SplitFlapDisplay class
        pass
