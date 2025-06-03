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

import crcmod
import socket
import time

from PIL import Image, ImageOps, ImageSequence


class VistraI:
    """
    A VISTRA-I display
    
    Please note that currently only Ethernet connection is supported.
    """
    
    MSG_TYPE_CLEAR_PANEL = 0x01
    MSG_TYPE_NULL = 0x06
    MSG_TYPE_SET_BRIGHTNESS = 0x08
    MSG_TYPE_TEXT = 0x0B
    MSG_TYPE_CLEAR_WINDOW = 0x0C
    MSG_TYPE_GRAPHICS = 0x0E
    MSG_TYPE_GET_BITMAP = 0xF2
    MSG_TYPE_GET_TEXT_OBJECTS = 0xF5
    
    EFFECT_NONE = 0x00
    EFFECT_BLINK = 0x01
    EFFECT_SCROLL_ALTERNATE = 0x02
    EFFECT_SCROLL = 0x04
    EFFECT_SCROLL_VERTICAL = 0x08
    EFFECT_CENTERED = 0x10
    EFFECT_RIGHT = 0x20
    EFFECT_MIDDLE = 0x40
    EFFECT_BOTTOM = 0x80

    EFFECT3_NONE = 0x00
    EFFECT3_DEF = 0x03 # purpose unclear
    EFFECT3_WINDOW_INVERTED = 0x40
    EFFECT3_INVERTED = 0x50
    
    def __init__(self, hostname, port, address = 0, timeout = 5.0, encoding_errors = "replace"):
        """
        hostname:
        The network hostname of the display to connect to
        
        port:
        The TCP port to use for communication
        
        address:
        The panel address (0 for all panels, only useful for RS232)
        
        timeout:
        Timeout for socket connection in seconds
        
        encoding_errors:
        Which error handler to use in case of encoding errors
        """
        
        self.hostname = hostname
        self.port = port
        self.address = address
        self.timeout = timeout
        self.encoding_errors = encoding_errors
        self.crc = crcmod.predefined.mkPredefinedCrcFun('crc-ccitt-false')
        self.queue = None
        self.socket = None
        self.last_transmission = 0
        #self.renew_socket()
    
    def renew_socket(self):
        """
        Renew the socket in case it got fucked up
        """
        
        try:
            self.socket.close()
        except:
            pass
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)
        self.socket.connect((self.hostname, self.port))
        #print("Socket renewed.")
    
    def init_queue(self):
        """
        Start collecting messages for bulk sending
        instead of directly sending them.
        """
        
        self.queue = []
    
    def send_queue(self):
        """
        Send all collected messages in bulk.
        """
        
        queue = self.queue
        self.queue = None
        reply = self.send_message(queue)
        return reply
    
    def wrap_message(self, message):
        """
        Add the start bytes and end byte to a message.
        
        message:
        The message as a bytestring
        """
        
        message = bytearray([0x02, self.address]) + message
        message += bytearray([0x03])
        return message
    
    def wrap_partial_message(self, message):
        """
        Add the start byte and CRC to a message.
        
        message:
        The message as a bytestring
        """
        
        crc = self.crc(message)
        crc_msb = crc >> 8
        crc_lsb = crc & 0xFF
        message = bytearray([0x1B]) + message
        message += bytearray([crc_lsb, crc_msb])
        return message
    
    def send_raw_message(self, message):
        """
        Send a raw message to the display.
        
        message:
        The message as a bytestring
        """
        
        try:
            #print(message)
            self.socket.send(message)
            # Receive up until the "RequestedDataType" byte
            reply = bytearray(self.socket.recv(9))
            #print(reply)
            data_type = reply[8]
            if data_type != 0x00:
                # Receive data length
                reply += bytearray(self.socket.recv(4))
                length = (
                    (reply[12] << 24)
                    | (reply[11] << 16)
                    | (reply[10] << 8)
                    | reply[9])
                # Receive the rest of the data
                reply += bytearray(self.socket.recv(length+1)) # +1 for end byte
            else:
                # Receive end byte
                reply += bytearray(self.socket.recv(1))
            self.last_transmission = time.time()
            return reply
        except socket.timeout:
            # Silently try to renew socket and fail silently
            try:
                self.renew_socket()
            except:
                pass
            raise
    
    def send_message(self, message):
        """
        Send a message to the display OR queue it if the queue mode is enabled.
        
        message:
        The message as a dict of attributes OR a list of message dicts.
        Example:
            {
                'msgType': 0...255,
                'attr2': 0...255,
                'attr3': 0...255,
                'font': 0...255,
                'winX': 0...65535,
                'winY': 0...65535,
                'winWidth': 0...65535,
                'winHeight': 0...65535,
                'data': bytearray([0x00, 0xFF])
            }
        """
        
        if type(message) not in (list, tuple):
            message = [message]
        
        if self.queue is not None:
            self.queue += message
            return
        
        complete_message = bytearray()
        for m in message:
            msg = bytearray([
                m.get('msgType', self.MSG_TYPE_TEXT),
                m.get('attr2', 0),
                m.get('attr3', 0),
                m.get('font', 0),
                (m.get('winX', 0) & (2**16-1)) & 0xFF, # support for negative values
                (m.get('winX', 0) & (2**16-1)) >> 8,
                (m.get('winY', 0) & (2**16-1)) & 0xFF,
                (m.get('winY', 0) & (2**16-1)) >> 8,
                (m.get('winWidth', 0) & (2**16-1)) & 0xFF,
                (m.get('winWidth', 0) & (2**16-1)) >> 8,
                (m.get('winHeight', 0) & (2**16-1)) & 0xFF,
                (m.get('winHeight', 0) & (2**16-1)) >> 8,
                len(m.get('data', bytearray())) & 0xFF,
                len(m.get('data', bytearray())) >> 8
            ])
            data = m.get('data', bytearray())
            if type(data) is str:
                data = data.encode('latin-1', errors=self.encoding_errors)
            msg += bytearray(data)
            msg = self.wrap_partial_message(msg)
            complete_message += msg
        
        complete_message = self.wrap_message(complete_message)
        # Renew socket if necessary
        if time.time() - self.last_transmission > 300: # 5 minutes
            self.renew_socket()
        return self.send_raw_message(complete_message)
    
    def clear_panel(self):
        """
        Clear all panel contents.
        """
        
        message = {'msgType': self.MSG_TYPE_CLEAR_PANEL}
        return self.send_message(message)
    
    def null_cmd(self):
        """
        Send a null command to keep communication going.
        """
        
        message = {'msgType': self.MSG_TYPE_NULL}
        return self.send_message(message)
    
    def set_brightness(self, brightness):
        """
        Set the base display brightness.
        
        brightness:
        The brightness level (0...255)
        """
        
        message = {
            'msgType': self.MSG_TYPE_SET_BRIGHTNESS,
            'data': [brightness]
        }
        return self.send_message(message)
    
    def clear_window(self, x = 0, y = 0):
        """
        Clear a window specified by the x and y coordinates.
        
        x, y:
        The coordinates of the window to be cleared
        """
        
        message = {
            'msgType': self.MSG_TYPE_CLEAR_WINDOW,
            'winX': x,
            'winY': y
        }
        return self.send_message(message)
    
    def send_text(self, text = "", font = 0,
        x = 0, y = 0, width = 0, height = 0,
        effects = EFFECT_NONE, effects3 = EFFECT3_NONE):
        """
        Send a text to the display.
        
        text:
        The text to send
        
        font:
        The ID of the font to use
        
        x, y:
        x and y coordinates of the top left window corner
        
        width, height:
        Window size
        
        effects:
        The effects to apply to the text (OR of the effect flags defined above)
        
        effects3:
        Some further effects
        """
        
        message = {
            'msgType': self.MSG_TYPE_TEXT,
            'attr2': effects,
            'attr3': effects3,
            'font': font,
            'winX': x,
            'winY': y,
            'winWidth': width,
            'winHeight': height,
            'data': text
        }
        return self.send_message(message)
    
    def send_image(self, image, invert = False,
        x = 0, y = 0, width = 0, height = 0,
        effects = EFFECT_NONE, effects3 = EFFECT3_NONE):
        """
        Send an image to the display.
        
        image:
        The image to send (file path, open file or Image instance)
        
        invert:
        Whether to invert the colors before sending
        
        x, y:
        x and y coordinates of the top left window corner
        
        width, height:
        Window size
        
        effects:
        The effects to apply to the image (OR of the effect flags defined above)
        
        effects3:
        Some further effects
        """
        
        if not isinstance(image, Image.Image):
            image = Image.open(image)
        
        image = image.convert("L")
        if invert:
            image = ImageOps.invert(image)
        im_width, im_height = image.size
        pixels = image.load()
        
        data = [
            im_width & 0xFF,
            im_width >> 8,
            im_height & 0xFF,
            im_height >> 8,
            0x00,
            0x00
        ]
        
        for im_y in range(0, im_height, 8):
            for im_x in range(im_width):
                byte = 0x00
                for im_yoff in range(7, -1, -1):
                    try:
                        byte |= (pixels[im_x, im_y+im_yoff] > 127) << im_yoff
                    except IndexError:
                        byte |= 1 << im_yoff
                data.append(byte)
        
        message = {
            'msgType': self.MSG_TYPE_GRAPHICS,
            'attr2': effects,
            'attr3': effects3,
            'winX': x,
            'winY': y,
            'winWidth': width,
            'winHeight': height,
            'data': data
        }
        return self.send_message(message)
    
    def send_gif(self, image, delay = 0.1, *args, **kwargs):
        """
        Send an animated GIF (one cycle).
        
        image:
        The image to send
        """
        
        if not isinstance(image, Image.Image):
            img = Image.open(image)
        else:
            img = image
        
        for frame in ImageSequence.Iterator(img):
            self.send_image(frame, *args, **kwargs)
            time.sleep(delay)
    
    def get_bitmap(self):
        """
        Get the current display bitmap.
        
        Returns:
        A PIL Image representing the current bitmap
        """
        
        message = {
            'msgType': self.MSG_TYPE_GET_BITMAP
        }
        response = self.send_message(message)
        img_info = response[13:19]
        img_data = response[19:-1]
        width = (img_info[1] << 8) | img_info[0]
        height = (img_info[3] << 8) | img_info[2]
        img = Image.new("RGB", (width, height))
        pixels = img.load()
        for i, byte in enumerate(img_data):
            x = i%width
            y_base = i//width * 8
            for n in range(8):
                y = y_base + n
                active = bool((byte >> n) & 0x01)
                pixels[x, y] = (255, 215, 0) if active else (0, 0, 0)
        return img
    
    #TODO
    def get_text_objects(self):
        """
        Get the current text objects.
        
        Returns:
        ???
        """
        
        message = {
            'msgType': self.MSG_TYPE_GET_TEXT_OBJECTS
        }
        response = self.send_message(message)
        return response