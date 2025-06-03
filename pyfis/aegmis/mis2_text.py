"""
Copyright (C) 2021-2025 Julian Metzler

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

from .mis2_protocol import MIS2Protocol

from ..utils import debug_hex
from ..utils.base_serial import BaseSerialPort


class MIS2TextDisplay(MIS2Protocol):
    ALIGN_LEFT = 0x00
    ALIGN_RIGHT = 0x01
    ALIGN_CENTER = 0x02
    
    ATTR_BLINK = 0x01
    ATTR_INVERT = 0x10
    ATTR_BLINK_INV = 0x08
    
    def merge_attributes(self, text):
        if type(text) in (tuple, list):
            merged = ""
            for t, attrs in text:
                merged += "\x00" + chr(attrs) + t
            return merged
        return text

    def text(self, page, row, col_start, col_end, text, attrs = ALIGN_LEFT):
        # Page 0xFF is the fallback page and will be saved permanently
        # Page 0xFE copies the page to all 10 slots
        text = self.merge_attributes(text)
        text = text.encode("CP437", errors=self.encoding_errors)
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
