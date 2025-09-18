"""
Copyright (C) 2025 Julian Metzler

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

from ..utils import debug_hex, high16, low16


class MobitecMatrix:
    CMD_TEXT = 0xA2
    CMD_TEST = 0xA4
    CMD_EFFECT_TEXT = 0xA5
    CMD_VERSION_INFO = 0xA6

    ATTR_DISPLAY_WIDTH = 0xD0
    ATTR_DISPLAY_HEIGHT = 0xD1
    ATTR_POS_X = 0xD2
    ATTR_POS_Y = 0xD3
    ATTR_FONT = 0xD4
    ATTR_SCROLL_PARAMS = 0xD5

    EFFECT_NONE = 0x00 # No effect
    EFFECT_SCROLL_RTL_ONCE = 0x01 # Scroll from right to left until left area border is reached
    EFFECT_SCROLL_LTR_ONCE = 0x02 # Scroll from left to right until right area border is reached
    EFFECT_SCROLL_BTT_ONCE = 0x03 # Scroll from bottom to top until area upper border is reached
    EFFECT_SCROLL_TTB_ONCE = 0x04 # Scroll from top to bottom until area bottom border is reached
    EFFECT_SCROLL_RTL = 0x05 # Continuously scroll from right to left
    EFFECT_SCROLL_LTR = 0x06 # Continuously scroll from left to right
    EFFECT_SCROLL_BTT = 0x07 # Continuously scroll from bottom to top
    EFFECT_SCROLL_TTB = 0x08 # Continuously scroll from top to bottom
    EFFECT_BLINK = 0x09 # Blinking text
    EFFECT_SCROLL_RTL_CENTER = 0x0A # Scroll from right to left until text is horizontally centered
    EFFECT_SCROLL_LTR_CENTER = 0x0B # Scroll from left to right until text is horizontally centered
    EFFECT_SCROLL_BTT_CENTER = 0x0C # Scroll from bottom to top until text is vertically centered
    EFFECT_SCROLL_TTB_CENTER = 0x0D # Scroll from top to bottom until text is vertically centered
    EFFECT_SCROLL_L_R_CENTER = 0x10 # Scroll left to right and right to left simultaneously until horizontally centered
    EFFECT_EXPLODE = 0x11 # Exploding
    EFFECT_CENTER_SCROLL_RTL_CENTER = 0x12 # Centered text and then same text scrolled to centered from right

    def __init__(self, port, address, exclusive=True, debug=False, encoding_errors="strict"):
        self.port = port
        self.address = address
        self.debug = debug
        self.exclusive = exclusive
        self.encoding_errors = encoding_errors
        self.open()
    
    def open(self):
        if isinstance(self.port, serial.Serial):
            self.device = port
            self.port = self.device.port
        else:
            self.device = serial.Serial(self.port,
                baudrate=4800, bytesize=8, parity='N', stopbits=1, timeout=1.0, exclusive=self.exclusive)
    
    def close(self):
        self.device.close()
    
    def make_checksum(self, data):
        checksum_bytes = bytearray()
        checksum = sum(data) % 0x100
        if checksum == 0xFF:
            checksum_bytes.append(0xFE)
            checksum_bytes.append(0x01)
        elif checksum == 0xFE:
            checksum_bytes.append(0xFE)
            checksum_bytes.append(0x00)
        else:
            checksum_bytes.append(checksum)
        return checksum_bytes

    def make_command_frame(self, data):
        frame = bytearray()
        frame.append(0xFF)
        frame.append(self.address)
        frame += data
        checksum_data = bytearray([self.address]) + data
        frame += self.make_checksum(checksum_data)
        frame.append(0xFF)
        return frame

    def send_frame(self, frame):
        if self.debug:
            print("TX: " + debug_hex(frame, readable_ascii=False, readable_ctrl=False))
        self.device.write(frame)

    def make_static_text_field(self, text, x = 0, y = 0, font = None):
        """
        0xDA can be used inside the text to turn on inversion, 0xDB turns it off.
        """
        data = []
        data += [self.ATTR_POS_X, x]
        data += [self.ATTR_POS_Y, y]
        if font is not None:
            data += [self.ATTR_FONT, font]
        data += text.encode("latin-1", errors=self.encoding_errors)
        return data

    def make_effect_text_field(self, text, text_area, effect, effect_cycles = 0, effect_time = 0, effect_speed = 0, x = 0, y = 0, font = None):
        """
        text_area:     4-tuple or list in the form: (Upper left X, Upper left Y, Lower right X, Lower right Y)
                       Note: Lower right coordinates are EXCLUDING the given point
        effect:        See EFFECT_* definitions at the top of this class
        effect_cycles: EITHER number of scroll / blink cycles OR 0 to use total time instead of number of cycles
        effect_time:   IF effect_cycles is 0: Total time (in seconds) to show the effect, 0 means indefinitely
                       ELSE: Time (in seconds) between scroll text disappearing and reappearing
                       No effect if effect_cycles is NOT 0 and effect is EFFECT_BLINK.
        effect_speed:  IF effect is EFFECT_BLINK: Perios (in seconds) for blinking (i.e. 1x on + 1x off)
                       ELSE: Scroll speed in pixels per second
        """
        data = []
        data += [self.ATTR_SCROLL_PARAMS]
        data += text_area
        data += [effect, effect_cycles, effect_time, effect_speed]
        data += [self.ATTR_POS_X, x]
        data += [self.ATTR_POS_Y, y]
        if font is not None:
            data += [self.ATTR_FONT, font]
        data += text.encode("latin-1", errors=self.encoding_errors)
        return data

    def send_texts(self, texts, display_width = None, display_height = None, use_effects = False):
        """
        texts has to be a list or tuple of dicts as follows:
        {
            "text": "Hello world",
            "duration": 3, [optional, see below]
            "x": 10,
            "y": 0,
            "font": 0x65,

            [below entries are only required if use_effects is True - see make_effect_text_field]
            "area": (0, 0, 144, 16),
            "effect": EFFECT_SCROLL_RTL,
            "effect_cycles": 3,
            "effect_time": 1,
            "effect_speed": 50
        }
        duration is in seconds.
        NOTE: There seems to be something weird going on with the duration parameter.
        If it is added after each text, the duration is correctly set for each text,
        but there will be a blank text with the same duration as the first text inbetween.
        To circumvent this, omit the duration parameter in the last text.
        This will cause it to have the same duration as the first text, however.
        It seems this is a necessary tradeoff.
        This also allows you to specify multiple texts without a duration. If you do this,
        all the texts without a duration up to and including the next one WITH a duration
        will be shown together.
        """
        data = [self.CMD_EFFECT_TEXT if use_effects else self.CMD_TEXT]
        if display_width is not None:
            data += [self.ATTR_DISPLAY_WIDTH, display_width]
        if display_height is not None:
            data += [self.ATTR_DISPLAY_HEIGHT, display_height]
        num_texts = len(texts)

        for text in texts:
            if use_effects:
                data += self.make_effect_text_field(text['text'], text['area'], text['effect'], text['effect_cycles'], text['effect_time'], text['effect_speed'], text['x'], text['y'], text['font'])
            else:
                data += self.make_static_text_field(text['text'], text['x'], text['y'], text['font'])
            if 'duration' in text:
                data += [0xB0, text['duration']]

        frame = self.make_command_frame(bytearray(data))
        self.send_frame(frame)

    def send_static_text(self, text, x = 0, y = 0, font = None, display_width = None, display_height = None):
        texts = [{
            'text': text,
            'x': x,
            'y': y,
            'font': font
        }]
        self.send_texts(texts, display_width, display_height, use_effects=False)

    def send_effect_text(self, text, text_area, effect, effect_cycles = 0, effect_time = 0, effect_speed = 0, x = 0, y = 0, font = None, display_width = None, display_height = None):
        texts = [{
            'text': text,
            'x': x,
            'y': y,
            'font': font,
            'area': text_area,
            'effect': effect,
            'effect_cycles': effect_cycles,
            'effect_time': effect_time,
            'effect_speed': effect_speed
        }]
        self.send_texts(texts, display_width, display_height, use_effects=True)

    def show_version_info(self):
        frame = self.make_command_frame(bytearray([self.CMD_VERSION_INFO]))
        self.send_frame(frame)

    def echo_byte(self, byte):
        # Causes the display to send back the specified byte for testing communication
        frame = self.make_command_frame(bytearray([self.CMD_TEST, 0x00, byte]))
        self.send_frame(frame)
        return self.device.read(1)