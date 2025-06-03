"""
Copyright (C) 2023-2025 Julian Metzler

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


class AesysDSA:
    def __init__(self, port, exclusive=True, debug=False, encoding_errors="strict"):
        self.port = port
        self.debug = debug
        self.exclusive = exclusive
        self.encoding_errors = encoding_errors
        self.open()
    
    def open(self):
        self.device = serial.Serial(self.port,
            baudrate=9600, bytesize=8, parity='N', stopbits=1, exclusive=self.exclusive)
    
    def close(self):
        self.device.close()
    
    def _checksum(self, data):
        checksum = sum(data)
        data += "{:04X}".format(checksum & 0xFFFF).encode('ascii')
        return data
    
    def send_text(self, text):
        data = "\x01\x17P000060{text}".format(text=text)
        length = len(data)
        frame = "\x02AVIS{length:04X}{data}\x03".format(length=length, data=data)
        frame = frame.encode('cp850', errors=self.encoding_errors)
        frame = self._checksum(frame)
        if self.debug:
            print(frame)
        self.device.write(frame)