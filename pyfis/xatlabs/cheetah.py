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

import base64
import requests

from PIL import Image

from ..splitflap_display import SplitFlapDisplay, TextField, CustomMapField


class xatLabsCheetah:
    """
    Controls the xatLabs Cheetah universal display controller.
    This uses TCP-based protocol in which the framebuffer is
    transmitted as a Base64 encoded string.
    The reason it's done this was is to allow transferring the
    framebuffer inside a JSON object.
    Cheetah supports various types of displays, including:
    - Pixel-based displays (Only 1bpp pixel buffer supported so far)
    - Character-based displays (e.g. a character LCD or alphanumerical split-flap display)
    - Selection-based displays (e.g. a rolling film or generic split-flap display)
    """

    def __init__(self, host = None, display_info = None, device_info = None, encoding_errors = "strict"):
        self.host = host
        self.display_info = display_info
        self.device_info = device_info
        self.encoding_errors = encoding_errors
        if self.host is not None:
            self.load_display_info()
            self.load_device_info()
        elif self.display_info is None or self.device_info is None:
            raise ValueError("Either host or display_info and device_info must be given")
        self.init_buffers()

    def init_buffers(self):
        self.pixel_buffer = None
        self.text_buffer = None
        self.unit_buffer = None
        
        pixbuf_size = self.display_info.get('pixbuf_size')
        if pixbuf_size is not None:
            self.pixel_buffer = [0] * pixbuf_size
        
        textbuf_size = self.display_info.get('textbuf_size')
        if textbuf_size is not None:
            self.text_buffer = [0] * textbuf_size
        
        unitbuf_size = self.display_info.get('unitbuf_size')
        if unitbuf_size is not None:
            self.unit_buffer = [0] * unitbuf_size

    def load_display_info(self):
        resp = requests.get(f"{self.host}/info/display.json")
        self.display_info = resp.json()

    def load_device_info(self):
        resp = requests.get(f"{self.host}/info/device.json")
        self.device_info = resp.json()
    
    def buffer_to_base64(self, buffer):
        buf = bytearray(buffer)
        return base64.b64encode(buf).decode('ascii')
    
    def update_pixel_buffer(self, image):
        self.pixel_buffer = [0] * len(self.pixel_buffer)
        if type(image) in (list, tuple):
            buf = image[:len(self.pixel_buffer)]
        else:
            if not isinstance(image, Image.Image):
                image = Image.open(image)
            pixbuf_type = self.display_info.get('pixbuf_type')
            frame_width = self.display_info.get('frame_width_pixel')
            frame_height = self.display_info.get('frame_height_pixel')
            image_width, image_height = image.size
            if pixbuf_type == '1bpp':
                image = image.convert('L')
                pixels = image.load()
                buf = []
                for x in range(image_width):
                    for y in range(0, image_height, 8):
                        byte = 0
                        for bit in range(8):
                            if y + bit < image_height:
                                byte = (byte >> 1) | ((1 if pixels[x, y + bit] > 127 else 0) << 7)
                            else:
                                byte >>= 1
                        buf.append(byte)
            else:
                raise NotImplementedError(f"{pixbuf_type} pixel buffer not yet supported")
        for i in range(len(self.pixel_buffer)):
            if i < len(buf):
                self.pixel_buffer[i] = buf[i]
            else:
                self.pixel_buffer[i] = 0
    
    def update_text_buffer(self, text):
        characters = text.encode('iso-8859-1', errors=self.encoding_errors)
        for i in range(len(self.text_buffer)):
            if i < len(characters):
                self.text_buffer[i] = characters[i]
            else:
                self.text_buffer[i] = 0

    def update_unit_buffer(self, module_data):
        self.unit_buffer = [0] * len(self.unit_buffer)
        for pos, val in module_data.items():
            self.unit_buffer[pos] = int(val)

    def set_brightness(self, brightness):
        if not self.display_info.get('brightness_control'):
            raise NotImplementedError("Display does not support brightness control")
        assert brightness in range(0, 256)
        if self.host is not None:
            requests.post(f"{self.host}/canvas/brightness.json", json={'brightness': brightness})

    def set_image(self, image):
        if self.display_info.get('pixbuf_size') is None:
            raise NotImplementedError("Display does not have a pixel buffer")
        self.update_pixel_buffer(image)
        if self.host is not None:
            buffer_b64 = self.buffer_to_base64(self.pixel_buffer)
            requests.post(f"{self.host}/canvas/buffer/pixel", data=buffer_b64)

    def set_text(self, text):
        if self.display_info.get('textbuf_size') is None:
            raise NotImplementedError("Display does not have a text buffer")
        self.update_text_buffer(text)
        if self.host is not None:
            buffer_b64 = self.buffer_to_base64(self.text_buffer)
            requests.post(f"{self.host}/canvas/buffer/text", data=buffer_b64)

    def d_set_module_data(self, module_data):
        # Compatibility function for SplitFlapDisplay class
        self.update_unit_buffer(dict(module_data))

    def d_update(self):
        # Compatibility function for SplitFlapDisplay class
        if self.display_info.get('unitbuf_size') is None:
            raise NotImplementedError("Display does not have a unit buffer")
        if self.host is not None:
            buffer_b64 = self.buffer_to_base64(self.unit_buffer)
            requests.post(f"{self.host}/canvas/buffer/unit", data=buffer_b64)

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
