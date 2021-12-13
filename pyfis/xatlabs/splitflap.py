"""
Copyright (C) 2021 Julian Metzler

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


class xatLabsSplitFlapController:
    """
    Controls the xatLabs Arduino-based generic split-flap controller.
    This is basically just a very simple serial protocol for
    setting specified split-flap units to specified positions.
    """

    ACT_SET_SEQ = 0xA0  # Set units sequentially
    ACT_SET_ADDR = 0xA1 # Set units addressed
    ACT_SET_HOME = 0xA2 # Set all units to home
    ACT_UPDATE = 0xA3   # Start the units

    def __init__(self, port, debug = False, exclusive = True):
        self.debug = debug
        if isinstance(port, serial.Serial):
            self.port = port
        else:
            self.port = serial.Serial(port, baudrate=115200, timeout=2.0, exclusive=exclusive)

    def debug_message(self, message):
        """
        Turn a message into a readable form
        """
        result = ""
        for byte in message:
            if byte in range(0, 32) or byte >= 127:
                result += "<{:02X}>".format(byte)
            else:
                result += chr(byte)
            result += " "
        return result

    def read_response(self):
        """
        Read the response from the addressed station
        """
        response = self.port.read(1)
        if not response:
            raise CommunicationError("Timeout waiting for response")
        if self.debug:
            print("RX: " + self.debug_message(response))
        return response

    def send_command(self, action, payload):
        data = [0xFF, action, len(payload)] + payload
        print("TX: " + self.debug_message(data))
        self.port.write(bytearray(data))

    def send_command_with_response(self, action, payload):
        """
        Send a command and retrieve the response data
        """
        self.send_command(action, payload)
        return self.read_response()

    def set_home(self):
        """
        Set all units to their home position
        """
        return self.send_command_with_response(self.ACT_SET_HOME, [])

    def set_positions(self, positions):
        """
        Set all units with sequential addressing
        positions: list of positions for units starting at address 0
        """
        return self.send_command_with_response(self.ACT_SET_SEQ, positions)

    def set_positions_addressed(self, positions):
        """
        Set all units with explicit addressing
        positions: dict of format {address: position}
        """
        pos_map = [item for k in positions for item in (k, positions[k])]
        return self.send_command_with_response(self.ACT_SET_ADDR, pos_map)

    def update(self):
        """
        Start the update of all units
        """
        return self.send_command_with_response(self.ACT_UPDATE, [])

    def d_set_module_data(self, module_data):
        # Compatibility function for SplitFlapDisplay class
        self.set_positions_addressed(dict(module_data))

    def d_update(self):
        # Compatibility function for SplitFlapDisplay class
        self.update()
