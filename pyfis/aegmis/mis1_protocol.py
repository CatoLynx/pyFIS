"""
Copyright (C) 2020-2025 Julian Metzler

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

from .exceptions import CommunicationError, DisplayError
from ..utils import debug_hex
from ..utils.base_serial import BaseSerialPort


class MIS1Protocol:
    ERROR_CODES = {
        0:  "OK",
        1:  "EFONTSIZE",
        2:  "CLIPPED",
        5:  "ECHAR_ATTRIBUTE",
        6:  "EINIT_DISPLAY",
        8:  "ERANGE",
        11: "EOPTION",
        13: "EHWDISPLAY",
        15: "ESECTOR",
        16: "EPAGE",
        17: "BITMAP",
        19: "EBITMAP",
        20: "ELINE",
        24: "ESECTORNR",
        25: "EPAGENR",
        26: "ESECX",
        27: "ESECY",
        36: "EFONTNR",
        38: "EFONTMISS",
        57: "EALLOC",
        255: "EGENERAL"
    }

    def __init__(self, port, address=1, baudrate=9600, exclusive=True, debug=False, rx_timeout=3.0, use_rts=True, encoding_errors="strict"):
        self.address = address
        self.debug = debug
        self.rx_timeout = rx_timeout
        self.use_rts = use_rts
        self.encoding_errors = encoding_errors
        if isinstance(port, serial.Serial) or isinstance(port, BaseSerialPort):
            self.port = port
        else:
            self.port = serial.Serial(port, baudrate=baudrate, bytesize=8, parity="E", stopbits=1, exclusive=exclusive, timeout=rx_timeout)

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

    def unescape(self, data):
        unescaped = []
        escape_active = False
        for byte in data:
            if not escape_active and byte == 0x10:
                escape_active = True
            else:
                escape_active = False
                unescaped.append(byte)
        return unescaped
    
    def send_raw_data(self, data):
        if self.debug:
            print("TX: " + debug_hex(data, readable_ascii=False, readable_ctrl=False))
        if self.use_rts:
            self.port.setRTS(1)
        self.port.write(data)
        if self.use_rts:
            time.sleep(0.1)
            self.port.setRTS(0)
    
    def send_raw_telegram(self, data):
        telegram = [0x04, (0x80 | self.address), 0x02] + self.escape(data) + [0x03] + [self.checksum(data + [0x03])]
        self.send_raw_data(telegram)
    
    def send_command(self, code, subcode, data, expect_response=True):
        self.send_raw_telegram([code, subcode] + data)
        if expect_response:
            return self.read_response(ack=False)

    def send_tx_request(self):
        self.send_raw_data([0x04, (0x80 | self.address), 0x05])
        return self.read_response(ack=True)

    def read_response(self, ack=False):
        data = self.port.read(1)
        if not data:
            raise CommunicationError("No response received from display")

        start = data[0]
        if start in (0x06, 0x15):
            response = data
        else:
            while start != 0x02:
                data = self.port.read(1)
                if not data:
                    raise CommunicationError("No response received from display")
                start = data[0]

            response = [start]
            escape_active = False
            while True:
                data = self.port.read(1)
                if not data:
                    raise CommunicationError("No response received from display")
                byte = data[0]
                if not escape_active:
                    if byte == 0x10:
                        escape_active = True
                    elif byte == 0x03:
                        response.append(byte)
                        data = self.port.read(1)
                        if not data:
                            raise CommunicationError("No response received from display")
                        checksum = data[0]
                        response.append(checksum)
                        break
                    else:
                        response.append(byte)
                else:
                    escape_active = False
                    response.append(byte)

        if self.debug:
            print("RX: " + debug_hex(response, readable_ascii=False, readable_ctrl=False))

        # Send ACK if required and didn't get a NAK
        if ack and response != b'\x15':
            self.send_raw_data([0x06])
        return response

    def check_error(self, response):
        if len(response) < 7:
            return
        if response[1] != 0x8C:
            return
        data = self.unescape(response[3:-2])
        raise DisplayError(self.ERROR_CODES.get(data[1], str(data[1])))
