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

from ..utils import debug_hex


class MIS2GCUDisplay:
    ALIGN_LEFT = 0x00
    ALIGN_RIGHT = 0x01
    ALIGN_CENTER = 0x02
    
    ATTR_BLINK = 0x01
    ATTR_INVERT = 0x10
    ATTR_BLINK_INV = 0x08
    
    def __init__(self, port, address = 1, baudrate = 9600, exclusive = True, debug = False):
        self.address = address
        self.debug = debug
        if isinstance(port, serial.Serial):
            self.port = port
        else:
            self.port = serial.Serial(port, baudrate=baudrate, bytesize=8, parity="E", stopbits=1, exclusive=exclusive)

    def checksum(self, data):
        checksum = 0x00
        for i, byte in enumerate(data):
            checksum += byte + 1 # +1 per byte because the data length needs to be added to the checksum
        return (checksum % 256) | 0x80

    def escape(self, data):
        escaped = []
        for byte in data:
            if byte in (0x02, 0x03, 0x04, 0x05, 0x10, 0x17):
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
    
    def merge_attributes(self, text):
        if type(text) in (tuple, list):
            merged = ""
            for t, attrs in text:
                merged += "\x00" + chr(attrs) + t
            return merged
        return text

    def set_timeout(self, timeout):
        # Timeout in seconds, resolution 0.5s, range 0 ... 32767
        timeout = round(timeout * 2)
        return self.send_command(0x01, 0x00, [timeout >> 8, timeout & 0xFF])

    def text(self, page, row, col_start, col_end, text, attrs = ALIGN_LEFT):
        # Page 0xFF is the fallback page and will be saved permanently
        # Page 0xFE copies the page to all 10 slots
        text = self.merge_attributes(text)
        text = text.encode("CP437")
        data = [page, row, col_start >> 8, col_start & 0xFF, col_end >> 8, col_end & 0xFF, attrs] + list(text)
        return self.send_command(0x15, 0x00, data)

    def delete_line(self, page, line):
        return self.send_command(0x23, 0x00, [page, line])
    
    def set_pages(self, pages):
        # pages: List of tuples in the form
        # (page, duration) - duration in seconds, 0.5s resolution
        data = []
        for page, duration in pages:
            data.append(page)
            data.append(round(duration * 2))
        return self.send_command(0x24, 0x00, data)
    
    def set_page(self, page):
        return self.set_pages([(page, 10)])

    def copy_page(self, src_page, dest_page):
        return self.send_command(0x26, 0x00, [src_page, dest_page])

    def delete_page(self, page):
        return self.send_command(0x2F, 0x00, [page])

    def reset(self):
        return self.send_command(0x31, 0x00, [])

    def set_test_mode(self, state):
        return self.send_command(0x32, 0x00, [1 if state else 0])

    def sync(self):
        return self.send_command(0x34, 0x00, [])

    def set_outputs(self, state):
        return self.send_command(0x41, 0x00, [state])
