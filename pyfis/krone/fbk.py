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


class KroneFBKController:
    """
    Controls a FBK (Fallblatt-Buskopfkarte)
    (split-flap bus header) board which in turn
    controls a bunch of FBM split-flap modules.
    """
    
    BOARD_ID = 0xB2
    
    CTRL_READ = 0x81
    CTRL_WRITE_SINGLE_ACK = 0x82
    CTRL_WRITE_SINGLE_NOACK = 0x02
    CTRL_WRITE_BLOCK_ACK = 0x84
    CTRL_WRITE_BLOCK_NOACK = 0x04
    
    CMD_GET_STATUS = 0x01
    CMD_LOCK = 0xC6
    CMD_UNLOCK = 0xC7
    CMD_CONTROL = 0x0A

    def __init__(self, port, debug = False):
        self.debug = debug
        self.port = serial.Serial(port, baudrate=19200, timeout=1.0)
    
    def build_parameters(self, light, heater, fan, force_heater, force_fan, low_min_temp):
        """
        light: 1=on, 0=off
        heater: 1=on, 0=off
        fan: 1=on, 0=off
        force_heater: 1=force on, 0=automatic
        force_fan: 1=force on, 0=automatic
        low_min_temp: 1=-20°C temperature limit, 0=0°C temperature limit
        """
        parameter_byte = 0x00
        parameter_byte |= int(light) << 7
        parameter_byte |= int(heater) << 6
        parameter_byte |= int(fan) << 5
        parameter_byte |= int(force_heater) << 2
        parameter_byte |= int(force_fan) << 1
        parameter_byte |= int(low_min_temp)
        return parameter_byte
        
    def send_command(self, address, command, parameters = None, num_response_bytes = 0):
        if command == self.CMD_GET_STATUS:
            control = self.CTRL_READ
        elif command in (self.CMD_LOCK, self.CMD_UNLOCK, self.CMD_CONTROL):
            control = self.CTRL_WRITE_SINGLE_NOACK
        else:
            control = 0x00 # invalid
        
        data = [command]
        
        if parameters is not None:
            data.append(parameters)
        
        payload = [0xB2, address, 0x00, control, 0x01] + data + [0x00]
        length = len(payload)
        payload[2] = length
        
        checksum = 0x00
        for byte in payload:
            checksum ^= byte
        
        cmd_bytes = [0xFF, 0xFF] + payload + [checksum]
        
        if self.debug:
            print(" ".join((format(x, "02X") for x in cmd_bytes)))
        
        # Send it
        self.port.write(bytearray(cmd_bytes))

        # Read response
        if num_response_bytes > 0:
            return self.port.read(num_response_bytes)
        else:
            return None
    
    def send_heartbeat(self, address):
        cmd_bytes = [0xFF, 0xFF, 0x10, address, 0x00]
        if self.debug:
            print(" ".join((format(x, "02X") for x in cmd_bytes)))
        self.port.write(bytearray(cmd_bytes))
    
    def control(self, address, light, heater, fan, force_heater, force_fan, low_min_temp):
        return self.send_command(address, self.CMD_CONTROL, self.build_parameters(light, heater, fan, force_heater, force_fan, low_min_temp))
