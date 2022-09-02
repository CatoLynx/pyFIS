"""
Copyright (C) 2022 Julian Metzler

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

import math
import serial
import time

from .mis1_gcu import MIS1GCUDisplay
from ..utils.base_serial import BaseSerialPort


class MIS1Board:
    """
    A large board using multiple GCUs
    """
    
    def __init__(self, port, start_address = 1, num_rows = 1, rows_per_gcu = 8, baudrate = 9600, exclusive = True, debug = False):
        """
        port: Serial port for the GCU bus
        start_address: Address of the first GCU, usually 1
        num_rows: How many rows of text the board has
        rows_per_gcu: How many rows are controlled per GCU
        baudrate: GCU baudrate
        exclusive: Whether to lock the serial port for exclusive access
        debug: Enable debug output
        """
        self.start_address = start_address
        self.debug = debug
        self.num_rows = num_rows
        self.rows_per_gcu = rows_per_gcu
        
        if isinstance(port, serial.Serial) or isinstance(port, BaseSerialPort):
            self.port = port
        else:
            self.port = serial.Serial(port, baudrate=baudrate, bytesize=8, parity="E", stopbits=1, exclusive=exclusive)
            
        self.num_gcus = math.ceil(num_rows / rows_per_gcu)
        self.gcus = []
        self.gcu_outputs = []
        for i in range(self.start_address, self.start_address + self.num_gcus):
            self.gcus.append(MIS1GCUDisplay(self.port, i, debug=self.debug))
            self.gcu_outputs.append([0] * 8)
    
    def write_row(self, page, row, col, text):
        """
        Write text on specified page, row and column of the board (both starting at 0)
        """
        gcu_index = row // self.rows_per_gcu
        gcu_row = row % self.rows_per_gcu
        self.gcus[gcu_index].simple_text(page, gcu_row, col, text)
    
    def show_page(self, page):
        """
        Show the given page
        """
        for gcu in self.gcus:
            gcu.set_page(page)
    
    def show_pages(self, pages):
        """
        Show the given pages. Structure:
        [(page_num, page_duration), (page_num, page_duration)]
        where page_duration is as follows:
        0 = 0.0 s (invalid)
        1 = 0.5 s
        2 = 1.0 s
        ...
        254 = 127.0 s
        255 = 127.5 s (maximum)
        """
        for gcu in self.gcus:
            gcu.set_pages(pages)
    
    def write_text(self, page, start_row, start_col, text):
        """
        Write the given multiline text to the board on the given page
        and starting at the given row and column
        """
        lines = text.splitlines()
        for row in range(start_row, min(self.num_rows, start_row + len(lines))):
            self.write_row(page, row, start_col, lines[row - start_row])
    
    def set_blinker(self, row, state):
        """
        On boards with blinkers (like airport info boards), set the blinker
        for the given row active or inactive. This assumes the blinkers are
        controlled by the GPIOs of the GCU in ascending order.
        """
        gcu_index = row // self.rows_per_gcu
        gcu_row = row % self.rows_per_gcu
        self.gcu_outputs[gcu_index][gcu_row] = 1 if state else 0
    
    def update_blinkers(self):
        """
        Update the GPIOs according to the internal blinker states
        """
        for i, gcu in enumerate(self.gcus):
            gcu.set_outputs(self.gcu_outputs[i])
