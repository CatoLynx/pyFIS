"""
Copyright 2020 Julian Metzler

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


class KroneFBMController:
    """
    Controls one or several FBM (Fallblattmodul)
    (split flap module) boards.
    """
    
    CMD_SET_ALL = 0b0001
    CMD_SET_HOME = 0b0010
    CMD_RESET = 0b0011
    CMD_READ_STATUS = 0b0100
    CMD_READ_CODE = 0b0101
    CMD_LOCK = 0b0110
    CMD_UNLOCK = 0b0111
    CMD_SET_CODE = 0b1000
    CMD_START_CALIBRATION_BR2 = 0b1001
    CMD_START_CALIBRATION_BR1 = 0b1010
    CMD_STOP_CALIBRATION = 0b1011
    CMD_SET_TABLE = 0b1100

    def __init__(self, port, debug = False):
        self.debug = debug
        self.port = serial.Serial(port, baudrate=4800, parity=serial.PARITY_EVEN, timeout=1.0)
    
    def send_command(self, command, address = None, code = None, position = None, num_response_bytes = 0):
        # Build base command byte
        cmd_bytes = []
        cmd_base = 0b10010000

        # Address expansion bit
        if address is not None and address > 127:
            cmd_base |= 0b01000000
        
        # Code expansion bit
        if code is not None and code > 127:
            cmd_base |= 0b00100000
        
        # Command bits
        cmd_base |= command
        
        # Build the data to be sent
        cmd_bytes.append(cmd_base)
        if address is not None:
            cmd_bytes.append(address & 0b01111111)
        if code is not None:
            cmd_bytes.append(code & 0b01111111)
        if position is not None:
            cmd_bytes.append(position)
        
        if self.debug:
            print(" ".join((format(x, "#010b") for x in cmd_bytes)))
        
        # Send it
        self.port.write(bytearray(cmd_bytes))

        # Read response
        if num_response_bytes > 0:
            return self.port.read(num_response_bytes)
        else:
            return None
    
    def set_all(self):
        return self.send_command(self.CMD_SET_ALL)
    
    def set_home(self):
        return self.send_command(self.CMD_SET_HOME)
    
    def reset(self):
        return self.send_command(self.CMD_RESET)
    
    def read_status(self, address):
        return self.send_command(self.CMD_READ_STATUS, address, num_response_bytes=1)
    
    def read_code(self, address):
        return self.send_command(self.CMD_READ_CODE, address, num_response_bytes=1)
    
    def lock(self, address):
        return self.send_command(self.CMD_LOCK, address)
    
    def unlock(self, address):
        return self.send_command(self.CMD_UNLOCK, address)
    
    def set_code(self, address, code):
        return self.send_command(self.CMD_SET_CODE, address, code)
    
    def start_calibration_br2(self):
        return self.send_command(self.CMD_START_CALIBRATION_BR2)
    
    def start_calibration_br1(self):
        return self.send_command(self.CMD_START_CALIBRATION_BR1)
    
    def stop_calibration(self):
        return self.send_command(self.CMD_STOP_CALIBRATION)
    
    def set_table(self, address, code, position):
        return self.send_command(self.CMD_SET_TABLE, address, code, position)
    
    def set_text(self, text, start_address, length = None, descending = False):
        if length is not None:
            text = text[:length].ljust(length)
        for i, char in enumerate(text):
            address = start_address - i if descending else start_address + i
            self.set_code(address, ord(char.encode('iso-8859-1')))
    
    def d_set_module_data(self, module_data):
        # Compatibility function for SplitFlapDisplay class
        for addr, code in module_data:
            self.set_code(addr, code)
    
    def d_update(self):
        # Compatibility function for SplitFlapDisplay class
        self.set_all()