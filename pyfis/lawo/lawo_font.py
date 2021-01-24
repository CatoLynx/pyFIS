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
        self.name = None
        self.change_signature = None
        self.file_size = None
        self.file_name = None
        self.glyph_h = None
        self.baseline = None
        self.min_char = None
        self.max_char = None
        self.char_spacing = None
        self.preview_text = None
        self.num_blocks = None
        self.glyph_metadata = None
        self.glyph_data = None
        self.num_glyphs = None
        self.widest_glyph = None
        self.narrowest_glyph = None
        self.charset = None
    
    @staticmethod
    def _read_c_str(data):
        result = ""
        for byte in data:
            if byte == 0x00:
                return result
            else:
                result += bytes([byte]).decode('cp1252')
        return result
    
    @staticmethod
    def _read_until_double_null(data):
        result = ""
        for i, byte in enumerate(data):
            if byte == 0x00 and i < len(data) - 1 and data[i+1] == 0x00:
                return result
            else:
                result += bytes([byte]).decode('cp1252')
        return result
    
    @staticmethod
    def _chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    
    def read_file(self, file):
        with open(file, 'rb') as f:
            data = f.read()
        
        self.name = self._read_c_str(data[6:14]).strip()
        self.change_signature = data[16] << 8 | data[7] # Changes with every file change
        self.file_size = data[20] << 8 | data[21]
        self.file_name = self._read_c_str(data[32:45])
        self.glyph_h = data[45]
        self.baseline = data[46]
        self.min_char = data[47]
        self.max_char = data[48]
        self.char_spacing = data[52]
        self.preview_text = self._read_c_str(data[56:60])
        self.num_blocks = data[60] << 8 | data[61] # A block is a column of bytes with a length equal to the glyph height
        self.glyph_metadata = dict(zip(range(self.min_char, self.max_char+1), [None]*(self.max_char-self.min_char+1)))
        self.glyph_data = dict(zip(range(self.min_char, self.max_char+1), [None]*(self.max_char-self.min_char+1)))
        
        extra_data_start = 70 + 3 * (self.max_char - self.min_char + 1)
        if data[extra_data_start] == 0x00:
            # There is no extra data block, just skip the two 0x00 bytes
            glyph_data_block_start = extra_data_start + 2
        else:
            # There is an extra data block
            # Read it and skip the null terminator and the two 0x00 bytes
            self.extra_data = self._read_until_double_null(data[extra_data_start:])
            glyph_data_block_start = extra_data_start + len(self.extra_data) + 3
        
        self.num_glyphs = 0
        self.widest_glyph = 0
        self.narrowest_glyph = 255
        self.charset = ""
        for c in range(self.min_char, self.max_char+1):
            i = 70 + 3 * (c - self.min_char)
            self.glyph_metadata[c] = {
                'glyph_w': data[i],
                'offset': data[i+1] << 8 | data[i+2] # Offset from start of glyph data block in bits
            }
            if data[i] > 0:
                self.num_glyphs += 1
                self.charset += bytes([c]).decode('cp1252')
                if data[i] > self.widest_glyph:
                    self.widest_glyph = data[i]
                if data[i] < self.narrowest_glyph:
                    self.narrowest_glyph = data[i]
        
        for c in range(self.min_char, self.max_char+1):
            width = self.glyph_metadata[c]['glyph_w']
            glyph_start = glyph_data_block_start + self.glyph_metadata[c]['offset'] // 8
            i = glyph_start
            glyph_data = []
            for y in range(self.glyph_h):
                for x_byte in range(math.ceil(width / 8)):
                    glyph_data.append(data[i + x_byte])
                i += self.num_blocks
            self.glyph_data[c] = glyph_data
    
    def print_info(self):
        print("\n".join([f"Name:              {self.name}",
                         f"File Name:         {self.file_name}",
                         f"File Size:         {self.file_size} Bytes",
                         f"Change Sig:        {self.change_signature}",
                         f"Glyph Height:      {self.glyph_h} px",
                         f"Glyph Baseline:    {self.baseline} px",
                         f"Glyph Spacing:     {self.char_spacing} px",
                         f"Widest Glyph:      {self.widest_glyph} px",
                         f"Narrowest Glyph:   {self.narrowest_glyph} px",
                         f"Lowest Character:  {self.min_char} ({bytes([self.min_char]).decode('cp1252')})",
                         f"Highest Character: {self.max_char} ({bytes([self.max_char]).decode('cp1252')})",
                         f"Preview Text:      {self.preview_text}",
                         f"# Glyphs:          {self.num_glyphs}",
                         f"# Data Blocks:     {self.num_blocks}",
                         f"Character Set:     {self.charset}"]))
    
    def get_glyph_width(self, code):
        if code not in self.glyph_metadata:
            return 0
        return self.glyph_metadata[code]['glyph_w']
    
    def render_glyph(self, code):
        if code not in self.glyph_metadata:
            return None
        glyph_metadata = self.glyph_metadata[code]
        glyph_data = self.glyph_data[code]
        width = glyph_metadata['glyph_w']
        height = self.glyph_h
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
    
    def render_glyph_table(self, x_spacing=5, x_offset=25, y_spacing=5, row_min_height=12, num_cols=16):
        num_chars = self.max_char - self.min_char + 1
        
        # Calculate the displayed table range based on the font's character range
        # This new range is sure to leave no half filled rows
        table_range_min = self.min_char - (self.min_char % num_cols)
        table_range_max = self.max_char - (self.max_char % num_cols) + num_cols - 1
        
        row_list = range(table_range_min, table_range_max + 1, num_cols)
        num_rows = len(row_list)
        row_height = max(row_min_height, self.glyph_h) + y_spacing
        
        # Calculate widths of each column based on maximum glyph width in that column
        # taking into account spacings
        col_widths = {}
        for row, char_code_base in enumerate(row_list):
            for col in range(num_cols):
                char_code = char_code_base + col
                if char_code < 0 or char_code > 255:
                    continue
                if col not in col_widths or self.glyph_metadata.get(char_code, {'glyph_w': 0})['glyph_w'] + x_spacing + x_offset > col_widths[col]:
                    col_widths[col] = self.glyph_metadata[char_code]['glyph_w'] + x_spacing + x_offset
        
        # Calculate X start positions of each column
        x_tmp = 0
        col_offsets = {}
        for col, width in sorted(col_widths.items(), key=lambda i: i[0]):
            col_offsets[col] = x_tmp
            x_tmp += width
        
        # Calculate total glyph table dimensions
        width = sum(col_widths.values())
        height = num_rows * row_height
        
        # Create image
        table = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(table)
        font = ImageFont.truetype("arial.ttf", row_min_height)
        
        # Render grid, skipping the first row / column
        for row, char_code_base in list(enumerate(row_list))[1:]:
            y = row * row_height
            draw.line((0, y, width - 1, y), 255, 1)
        
        for col in range(1, num_cols):
            x = col_offsets[col]
            draw.line((x, 0, x, height - 1), 255, 1)
        
        # Render glyphs
        for row, char_code_base in enumerate(row_list):
            for col in range(num_cols):
                char_code = char_code_base + col
                x_base = col_offsets[col]
                y_base = row * row_height
                draw.text((x_base + 3, y_base), str(char_code), 255, font)
                glyph = self.render_glyph(char_code)
                if glyph:
                    table.paste(glyph, (x_base + x_offset + math.ceil(x_spacing / 2), y_base + math.ceil(y_spacing / 2)))
        
        return table
    
    def render_text(self, text):
        chars = bytes(text, 'cp1252', 'ignore')
        width = 0
        for code in chars:
            width += self.get_glyph_width(code) + self.char_spacing
        width -= self.char_spacing
        
        img = Image.new('L', (width, self.glyph_h), 0)
        x = 0
        for code in chars:
            glyph = self.render_glyph(code)
            img.paste(glyph, (x, 0))
            x += self.get_glyph_width(code) + self.char_spacing
        return img


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Tool for using LAWO font files")
    parser.add_argument("-f", "--file", type=str, required=True, help="Font file")
    parser.add_argument("-i", "--info", action='store_true', help="Show font info")
    parser.add_argument("-sg", "--show-glyph", type=int, required=False, help="Show glyph with given code")
    parser.add_argument("-gt", "--glyph-table", action='store_true', help="Show glyph table")
    parser.add_argument("-rt", "--render-text", type=str, required=False, help="Render given text")
    parser.add_argument("-o", "--output", type=str, required=False, help="Save output images to file instead of showing")
    args = parser.parse_args()
    
    font = LawoFont()
    font.read_file(args.file)
    
    if args.info:
        font.print_info()
    
    if args.render_text is not None:
        img = font.render_text(args.render_text)
        if args.output:
            img.save(args.output)
        else:
            img.show()
    elif args.glyph_table:
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
