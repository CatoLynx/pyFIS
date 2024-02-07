"""
Copyright (C) 2023-2024 Julian Metzler

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

import base64
import requests

from ..splitflap_display import SplitFlapDisplay, TextField, CustomMapField


class xatLabsCheetah:
    """
    Controls the xatLabs Cheetah universal display controller.
    This uses TCP-based protocol in which the framebuffer is
    transmitted as a Base64 encoded string.
    The reason it's done this was is to allow transferring the
    framebuffer inside a JSON object.
    Cheetah supports three types of displays:
    - Pixel-based displays (not yet implemented here)
    - Character-based displays (e.g. a character LCD or alphanumerical split-flap display)
    - Selection-based displays (e.g. a rolling film or generic split-flap display)
    """

    def __init__(self, host = None, display_info = None, device_info = None):
        self.host = host
        self.display_info = display_info
        self.device_info = device_info
        if self.host is not None:
            self.load_display_info()
            self.load_device_info()
        elif self.display_info is None or self.device_info is None:
            raise ValueError("Either host or display_info and device_info must be given")
        self.init_framebuf()

    def init_framebuf(self):
        display_type = self.display_info.get('type')
        if display_type == 'character':
            self.framebuf = [0] * self.display_info["charbuf_size"]
        elif display_type == 'selection':
            self.framebuf = [0] * self.display_info["framebuf_size"]
            if 'units' in self.display_info['config']:
                for unit in self.display_info['config']['units']:
                    if 'addr' in unit and 'home' in unit:
                        self.framebuf[unit['addr']] = unit['home']
        else:
            raise NotImplementedError("Unsupported display type: {}".format(display_type))

    def get_actual_char_count(self, s):
        count = 0
        if "combining_full_stop" in self.display_info["quirks"]:
            for i in range(len(s)):
                if i == 0:
                    count += 1  # Always count first character
                elif s[i] == ".":
                    if s[i-1] == ".":
                        count += 1  # Only count full stop if preceded by another full stop
                else:
                    count += 1  # Always count non full stop characters
        else:
            count = len(s)
        return count

    def update_framebuf_text(self, text):
        self.init_framebuf()
        val = ""
        for e in text.split("\n"):
            actual_len = self.get_actual_char_count(e)
            excess = actual_len - self.display_info["width"]
            if excess < 0:
                # Need to pad
                val += e.ljust(len(e) - excess, " ")
            else:
                # Need to cut off
                cutoff_pos = len(e) - excess
                val += e[:cutoff_pos]
        val_len = len(val)
        for i in range(self.display_info["charbuf_size"]):
            if i >= val_len:
                self.framebuf[i] = 0
            else:
                code = ord(val[i])
                self.framebuf[i] = code if code <= 255 else 0

    def update_framebuf_sel(self, module_data):
        self.init_framebuf()
        for pos, val in module_data.items():
            self.framebuf[pos] = int(val)

    def load_display_info(self):
        resp = requests.get(f"{self.host}/info/display.json")
        self.display_info = resp.json()

    def load_device_info(self):
        resp = requests.get(f"{self.host}/info/device.json")
        self.device_info = resp.json()
    
    def get_buffer_base64(self):
        buf = bytearray(self.framebuf)
        return base64.b64encode(buf).decode('ascii')

    def set_text(self, text):
        if self.display_info.get('type') != 'character':
            raise NotImplementedError("Only character displays support set_text")
        self.update_framebuf_text(text)
        if self.host is not None:
            buf = bytearray(self.framebuf)
            buffer_b64 = base64.b64encode(buf).decode('ascii')
            requests.post(f"{self.host}/canvas/buffer.json", json={'buffer': buffer_b64})

    def set_brightness(self, brightness):
        if not self.display_info.get('brightness_control'):
            raise NotImplementedError("Display does not support brightness control")
        assert brightness in range(0, 256)
        if self.host is not None:
            requests.post(f"{self.host}/canvas/brightness.json", json={'brightness': brightness})

    def d_set_module_data(self, module_data):
        # Compatibility function for SplitFlapDisplay class
        self.update_framebuf_sel(dict(module_data))

    def d_update(self):
        # Compatibility function for SplitFlapDisplay class
        if self.host is not None:
            buffer_b64 = self.get_buffer_base64()
            requests.post(f"{self.host}/canvas/buffer.json", json={'buffer': buffer_b64})

    def get_splitflap_display(self):
        if self.display_info.get('type') != 'selection':
            raise NotImplementedError("Only selection displays support get_splitflap_display")
        config = self.display_info.get('config', {})
        unit_data = config.get('units')
        if not unit_data:
            raise NotImplementedError("Display does not provide layout data")
        map_data = config.get('maps')
        if not map_data:
            raise NotImplementedError("Display does not provide mapping data")

        display = SplitFlapDisplay.from_json(config, self)
        return display