"""
Copyright (C) 2020-2021 Julian Metzler

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

from ..utils import debug_hex
from ..utils.base_serial import BaseSerialPort


class MIS1Protocol:
    def __init__(self, port, address = 1, baudrate = 9600, exclusive = True, debug = False):
        self.address = address
        self.debug = debug
        if isinstance(port, serial.Serial) or isinstance(port, BaseSerialPort):
            self.port = port
        else:
            self.port = serial.Serial(port, baudrate=baudrate, bytesize=8, parity="E", stopbits=1, exclusive=exclusive)

    def checksum(self, data):
        checksum = 0x00
        for i, byte in enumerate(data):
            checksum += byte
        return (checksum % 256) | 0x80

    def escape(self, data):
        escaped = []
        for byte in data:
            if byte in (0x02, 0x03, 0x04, 0x05, 0x10):
                escaped += [0x10, byte]
            else:
                escaped.append(byte)
        return escaped
    
    def send_raw_telegram(self, data):
        telegram = [0x04, (0x80 | self.address), 0x02] + self.escape(data) + [0x03] + [self.checksum(data + [0x03])]
        if self.debug:
            print(debug_hex(telegram, readable_ascii=False, readable_ctrl=False))
        self.port.setRTS(1)
        self.port.write(telegram)
        time.sleep(0.1)
        self.port.setRTS(0)
    
    def send_command(self, code, subcode, data):
        return self.send_raw_telegram([code, subcode] + data)
    
    def set_outputs(self, states):
        # states: array of 8 bools representing outputs 0 through 7
        state_byte = 0x00
        for i in range(max(8, len(states))):
            if states[i]:
                state_byte |= (1 << i)
        return self.send_command(0x41, 0x00, [0x00, 0x00, state_byte])
