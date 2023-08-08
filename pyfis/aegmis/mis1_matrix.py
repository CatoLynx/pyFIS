"""
Copyright (C) 2023 Julian Metzler

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

from PIL import Image

from .mis1_protocol import MIS1Protocol

from ..utils import debug_hex, high16, low16
from ..utils.base_serial import BaseSerialPort


class MIS1MatrixDisplay(MIS1Protocol):
    def set_config(self, lcd_module, num_lcds, x, y, id, board_timeout, fr_freq, fps, is_master, protocol_timeout, response_delay):
        # board_timeout: in seconds
        # protocol_timeout and response_delay: in milliseconds
        data = [
            high16(lcd_module),
            low16(lcd_module),
            num_lcds,
            high16(x),
            low16(x),
            high16(y),
            low16(y),
            high16(id),
            low16(id),
            high16(board_timeout * 2),
            low16(board_timeout * 2),
            fr_freq,
            fps,
            1 if is_master else 0,
            high16(protocol_timeout),
            low16(protocol_timeout),
            high16(response_delay),
            low16(response_delay),
            0x00,
            0x00
        ]
        return self.send_command(0x02, 0x00, data)

    def set_input_config(self, id, mask_byte, row_codes):
        data = [id, mask_byte]
        data.extend(row_codes)
        return self.send_command(0x04, 0x00, data)

    def text(self, board, page, font, x, y, width, text):
        data = [
            board,
            page,
            font,
            high16(x),
            low16(x),
            high16(y),
            low16(y),
            high16(width),
            low16(width)
        ]
        data.extend(bytearray(text, 'ascii'))
        return self.send_command(0x19, 0x00, data)

    def check_text_width(self, font, text):
        data = [0x00, font]
        data.extend(bytearray(text, 'ascii'))
        return self.send_command(0x1A, 0x00, data)

    def set_font_spacing(self, font_spacings):
        data = font_spacings
        return self.send_command(0x1F, 0x00, data)
    
    def set_pages(self, pages):
        flat_pages = [item for sublist in pages for item in sublist]
        data = [0x00, 0x00]
        data.extend(flat_pages)
        return self.send_command(0x24, 0x00, data)
    
    def set_page(self, page):
        return self.set_pages([(page, 255)])

    def copy_page(self, source, destination):
        data = [0x00, source, destination]
        return self.send_command(0x26, 0x00, data)

    def echo(self, number):
        data = [high16(number), low16(number)]
        return self.send_command(0x2A, 0x00, data)

    def set_pixel(self, page, x, y, state):
        data = [
            0x00,
            page,
            high16(x),
            low16(x),
            high16(y),
            low16(y),
            1 if state else 0
        ]
        return self.send_command(0x2B, 0x00, data)

    def fill_area(self, page, x, y, width, height, state):
        data = [
            0x00,
            page,
            high16(x),
            low16(x),
            high16(y),
            low16(y),
            high16(width),
            low16(width),
            high16(height),
            low16(height),
            1 if state else 0
        ]
        return self.send_command(0x2D, 0x00, data)

    def delete_scroll_sector(self, sector, page):
        data = [0x00, sector, page]
        return self.send_command(0x2E, 0x00, data)

    def delete_page(self, page):
        data = [0x00, page]
        return self.send_command(0x2F, 0x00, data)

    def reset(self):
        return self.send_command(0x31, 0x00, [])

    def set_test_mode(self, state):
        return self.send_command(0x32, 0x00, [1 if state else 0])

    def sync(self):
        return self.send_command(0x34, 0x00, [])

    def get_defective_rows(self):
        return self.send_command(0x35, 0x00, [])

    def get_config(self):
        return self.send_command(0x38, 0x00, [])

    def get_font_info(self):
        return self.send_command(0x39, 0x00, [])

    def partial_page_update(self, page, x, y, height, width):
        data = [
            0x00,
            0x00,
            page,
            high16(x),
            low16(x),
            high16(y),
            low16(y),
            high16(height),
            low16(height),
            high16(width),
            low16(width)
        ]
        return self.send_command(0x3A, 0x00, data)

    def get_id(self):
        return self.send_command(0x3E, 0x00, [])
    
    def set_outputs(self, states):
        # states: array of 8 bools representing outputs 0 through 7
        state_byte = 0x00
        for i in range(max(8, len(states))):
            if states[i]:
                state_byte |= (1 << i)
        return self.send_command(0x41, 0x00, [0x00, 0x00, state_byte])

    def read_inputs(self, id):
        data = [id]
        return self.send_command(0x42, 0x00, data)

    def set_vlcd(self, voltage):
        ones = int(voltage)
        decimals = round((voltage % 1) * 100)
        data = [ones, decimals]
        return self.send_command(0x61, 0x00, data)

    def get_firmware_revision(self):
        return self.send_command(0x65, 0x00, [])

    def get_temperature(self):
        return self.send_command(0x6A, 0x00, [])

    def get_vlcd(self):
        return self.send_command(0x6E, 0x00, [])

    def image_data(self, page, x, y, width, pixels):
        data = [
            0x00,
            0x00,
            page,
            high16(x),
            low16(x),
            high16(y),
            low16(y),
            high16(width),
            low16(width)
        ]
        data.extend(pixels)
        return self.send_command(0x73, 0x00, data)

    def scroll_image_data(self, sector, page, y, pixels):
        data = [
            0x00,
            0x00,
            sector,
            page,
            high16(y),
            low16(y)
        ]
        data.extend(pixels)
        return self.send_command(0x74, 0x00, data)

    def create_scroll_area(self, sector, page, x, y, width, height, data_width):
        data = [
            0x00,
            0x00,
            sector,
            page,
            high16(x),
            low16(x),
            high16(y),
            low16(y),
            high16(width),
            low16(width),
            high16(height),
            low16(height),
            high16(data_width),
            low16(data_width)
        ]
        return self.send_command(0x75, 0x00, data)

    def set_flash_cycle(self, cycle_time):
        data = [cycle_time]
        return self.send_command(0x7C, 0x00, data)

    def become_slave(self):
        return self.send_command(0x7D, 0x00, [])

    def become_master(self):
        return self.send_command(0x7E, 0x00, [])

    def dummy(self):
        return self.send_command(0x7F, 0x00, [])

    def image(self, page, x, y, image):
        if not isinstance(image, Image.Image):
            image = Image.open(image)
        image = image.convert('L')
        pixels = image.load()
        width, height = image.size
        for y_offset in range(height):
            _y = y + y_offset
            pixel_data = []
            byte = 0x00
            x_bit = 7
            for x_offset in range(width):
                if pixels[x_offset, y_offset] > 127:
                    byte |= (1 << x_bit)
                if x_bit == 0 or x_offset == width - 1:
                    x_bit = 7
                    pixel_data.append(byte)
                    byte = 0x00
                else:
                    x_bit -= 1
            self.image_data(page, x, _y, width, pixel_data)

    def scroll_image(self, sector, page, x, y, scroll_width, image, extra_whitespace=0):
        if not isinstance(image, Image.Image):
            image = Image.open(image)
        image = image.convert('L')
        pixels = image.load()
        width, height = image.size
        
        self.create_scroll_area(sector, page, x, y, scroll_width, height, width + extra_whitespace)
        for i in range(10):
            response = self.send_tx_request()
            self.check_error(response)

        for y_offset in range(height):
            _y = y + y_offset
            pixel_data = []
            byte = 0x00
            x_bit = 7
            for x_offset in range(width):
                if pixels[x_offset, y_offset] > 127:
                    byte |= (1 << x_bit)
                if x_bit == 0 or x_offset == width - 1:
                    x_bit = 7
                    pixel_data.append(byte)
                    byte = 0x00
                else:
                    x_bit -= 1
            self.scroll_image_data(sector, page, y_offset, pixel_data)

    def animation(self, sector_start, page, x, y, image):
        # Splits the animation into 1-pixel wide scroll sectors
        # that scroll through a spatial representation of the animation
        if not isinstance(image, Image.Image):
            image = Image.open(image)
        width, height = image.size

        orig_frames = []
        try:
            while True:
                orig_frames.append(image.convert('L').load())
                # Next frame
                image.seek(image.tell() + 1)
        except EOFError:
            pass

        num_frames = len(orig_frames)
        scroll_frames = []
        for i in range(width):
            scroll_frame = Image.new('L', (num_frames, height), 'black')
            scroll_pixels = scroll_frame.load()
            for _x, frame in enumerate(orig_frames):
                for _y in range(height):
                    scroll_pixels[_x, _y] = frame[i, _y]
            scroll_frames.append(scroll_frame)

        for _x, scroll_frame in enumerate(scroll_frames):
            self.scroll_image(sector_start + _x, page, x + _x, y, 1, scroll_frame)
