"""
Copyright (C) 2016 - 2021 Julian Metzler

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

import argparse
import crccheck
import math

from PIL import Image, ImageDraw, ImageFont
from pprint import pprint


class LawoFont:
    """
    LAWO font files, typically named FONTNAME.FXX, where XX is the glyph height
    """
    
    def __init__(self):
        self.info = {}
    
    @staticmethod
    def _read_c_str(data):
        result = ""
        for byte in data:
            if byte == 0x00:
                return result
            else:
                result += chr(byte)
        return result
    
    @staticmethod
    def _read_until_double_null(data):
        result = ""
        for i, byte in enumerate(data):
            if byte == 0x00 and i < len(data) - 1 and data[i+1] == 0x00:
                return result
            else:
                result += chr(byte)
        return result
    
    @staticmethod
    def _chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    
    def read_file(self, file):
        with open(file, 'rb') as f:
            data = f.read()
        
        self.info['font_name'] = self._read_c_str(data[6:14]).strip()
        self.info['change_signature'] = data[16] << 8 | data[7] # Changes with every file change
        self.info['file_size'] = data[20] << 8 | data[21]
        self.info['file_name'] = self._read_c_str(data[32:45])
        self.info['glyph_h'] = data[45]
        self.info['baseline'] = data[46]
        self.info['min_char'] = data[47]
        self.info['max_char'] = data[48]
        self.info['char_spacing'] = data[52]
        self.info['preview_text'] = self._read_c_str(data[56:60])
        self.info['num_blocks'] = data[60] << 8 | data[61] # A block is a column of bytes with a length equal to the glyph height
        self.info['glyph_metadata'] = dict(zip(range(data[47], data[48]+1), [None]*(data[48]-data[47]+1)))
        self.info['glyph_data'] = dict(zip(range(data[47], data[48]+1), [None]*(data[48]-data[47]+1)))
        
        extra_data_start = 70 + 3 * (data[48] - data[47] + 1)
        if data[extra_data_start] == 0x00:
            # There is no extra data block, just skip the two 0x00 bytes
            glyph_data_block_start = extra_data_start + 2
        else:
            # There is an extra data block
            # Read it and skip the null terminator and the two 0x00 bytes
            self.info['extra_data'] = self._read_until_double_null(data[extra_data_start:])
            glyph_data_block_start = extra_data_start + len(self.info['extra_data']) + 3
        self.info['glyph_data_block_start'] = glyph_data_block_start
        
        for c in range(data[47], data[48]+1):
            i = 70 + 3 * (c - data[47])
            self.info['glyph_metadata'][c] = {
                'glyph_w': data[i],
                'offset': data[i+1] << 8 | data[i+2] # Offset from start of glyph data block in bits
            }
        
        for c in range(data[47], data[48]+1):
            width = self.info['glyph_metadata'][c]['glyph_w']
            glyph_start = glyph_data_block_start + self.info['glyph_metadata'][c]['offset'] // 8
            i = glyph_start
            glyph_data = []
            for y in range(self.info['glyph_h']):
                for x_byte in range(math.ceil(width / 8)):
                    glyph_data.append(data[i + x_byte])
                i += self.info['num_blocks']
            self.info['glyph_data'][c] = glyph_data
    
    def print_info(self):
        pprint(self.info)
    
    def render_glyph(self, code):
        glyph_metadata = self.info['glyph_metadata'][code]
        glyph_data = self.info['glyph_data'][code]
        width = glyph_metadata['glyph_w']
        height = self.info['glyph_h']
        if width == 0:
            return None
        img = Image.new('L', (width, height), 0)
        px = img.load()
        i = 0
        for y in range(height):
            for x_byte in range(math.ceil(width / 8)):
                byte = glyph_data[i]
                for x_bit in range(8):
                    x = x_byte * 8 + 7 - x_bit
                    if x >= width:
                        continue
                    px[x,y] = 255 if (byte & (1 << x_bit)) else 0
                i += 1
        return img
    
    def render_glyph_table(self):
        num_chars = self.info['max_char'] - self.info['min_char'] + 1
        x_spacing = 5
        x_offset = 50
        y_spacing = 5
        row_min_height = 20
        width = max(map(lambda e: e['glyph_w'], self.info['glyph_metadata'].values())) + x_offset + x_spacing
        row_h = max(row_min_height, self.info['glyph_h'])
        height = row_h * num_chars + y_spacing * (num_chars - 1)
        table = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(table)
        font = ImageFont.truetype("arial.ttf", row_min_height)
        draw.line((x_offset - math.ceil(x_spacing / 2), 0, x_offset - math.ceil(x_spacing / 2), height - 1), 255, 1)
        for i, c in enumerate(range(self.info['min_char'], self.info['max_char'] + 1)):
            glyph = self.render_glyph(c)
            y = i * (row_h + y_spacing)
            draw.text((0, y), str(c), 255, font)
            if glyph:
                table.paste(glyph, (x_offset, y))
            if c < self.info['max_char']:
                draw.line((0, y + row_h + y_spacing // 2, width - 1, y + row_h + y_spacing // 2), 255, 1)
        return table


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=str, required=True)
    parser.add_argument("-i", "--info", action='store_true')
    parser.add_argument("-sg", "--show-glyph", type=int, required=False)
    parser.add_argument("-gt", "--glyph-table", action='store_true')
    parser.add_argument("-o", "--output", type=str, required=False)
    args = parser.parse_args()
    
    font = LawoFont()
    font.read_file(args.file)
    
    if args.info:
        font.print_info()
    
    if args.glyph_table:
        img = font.render_glyph_table()
        if args.output:
            img.save(args.output)
        else:
            img.show()
    elif args.show_glyph is not None:
        img = font.render_glyph(args.show_glyph)
        if img:
            if args.output:
                img.save(args.output)
            else:
                img.show()
        else:
            print("Glyph is empty")
