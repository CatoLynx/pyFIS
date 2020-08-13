"""
Copyright (C) 2020 Julian Metzler

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
import time

try:
    from PIL import Image
except ImportError:
    _HAS_PIL = False
else:
    _HAS_PIL = True

class MONOProtocol:
    """
    All the logic related to the MONO protocol
    """
    
    CMD_QUERY = 0x80
    CMD_PRE_BITMAP_FLIPDOT = 0x90
    CMD_COLUMN_DATA_FLIPDOT = 0xA0
    CMD_PRE_BITMAP_LED_1 = 0xB0
    CMD_PRE_BITMAP_LED_2 = 0xC0
    CMD_BITMAP_DATA_LED = 0xD0
    CMD_DISPLAY_BITMAP_LED = 0xE0
    
    def __init__(self, debug = False):
        """
        debug:
        Whether to print the sent and received frames
        """
        
        self.debug = debug
        self.connected_displays = {}
    
    def _send(self, frame):
        """
        Actually send the frame.
        This varies depending on implementation and needs to be overridden
        """
        pass
    
    def _receive(self, length):
        """
        Actually receive data.
        This varies depending on implementation and needs to be overridden
        """
        pass
    
    def set_display_attributes(self, address, attributes):
        """
        Set attributes of given display.
        Used internally to manage resolution.
        """
        
        self.connected_displays[address] = attributes.copy()
    
    def debug_frame(self, frame, receive = False):
        """
        Print a frame to standard output if the debug flag is set.
        
        frame:
        The frame to print
        
        receive:
        Whether to print the frame as sent or received
        """
        
        if self.debug:
            action = "Received" if receive else "Sending"
            frame_debug = " ".join("{:02X}".format(byte) for byte in frame)
            print("{} frame:".format(action))
            print(frame_debug)
    
    def checksum_led(self, payload):
        """
        MONO LED CHECKSUM: XOR every byte, start with 0xED
        
        payload:
        The payload to calculate the checksum for
        """
        
        chk = 0xED
        for b in payload:
            chk ^= b
        return chk
    
    def checksum_flipdot(self, payload):
        """
        MONO flipdot CHECKSUM: XOR every byte, start with 0xFF
        
        payload:
        The payload to calculate the checksum for
        """
        
        chk = 0xFF
        for b in payload:
            chk ^= b
        return chk
    
    def escape_frame(self, frame):
        """
        Escape the start/stop byte and the escape byte in the given frame.
        
        frame:
        The frame to escape.
        """
        
        escaped_frame = []
        for b in frame:
            if b == 0x7e:
                escaped_frame += [0x7d, 0x5e]
            elif b == 0x7d:
                escaped_frame += [0x7d, 0x5d]
            else:
                escaped_frame.append(b)
        return escaped_frame
    
    def prepare_frame(self, frame):
        """
        This function does the following:
        1. Escape the frame
        2. Prepend the start byte and append the stop byte
        
        frame:
        The frame (as a bytearray) to prepare
        
        Returns:
        The prepared frame (as a bytearray)
        """
        
        prepared_frame = self.escape_frame(frame)
        prepared_frame = [0x7e] + prepared_frame + [0x7e]
        return prepared_frame
    
    def send_frame(self, frame, reply_length = 0):
        """
        Send an arbitrary frame. Calls prepare_frame internally.
        
        frame:
        The frame to send
        
        reply_length:
        How many bytes to expect as a reply
        
        Returns:
        The received frame OR None
        
        TODO: Actually check the checksum
        """
        
        frame = bytearray(frame)
        frame = self.prepare_frame(frame)
        self.debug_frame(frame)
        self._send(frame)
        if reply_length:
            reply = self._receive(reply_length + 3)
            self.debug_frame(reply, receive=True)
            reply = reply[1:-2]
            return reply
    
    def get_command_byte(self, command, address):
        """
        Combine a command nibble with an address nibble.
        
        command:
        Command byte/nibble
        
        address:
        Address byte/nibble
        """
        
        return (command & 0xF0) | (address & 0x0F)
    
    def send_command(self, address, command, payload, reply_length = 0):
        """
        Send a command frame to a display.
        
        address:
        The bus address of the display (0x00 ... 0x0F)
        
        command:
        The command byte (0x00 ... 0xF0, upper 4 bits only)
        
        payload:
        The payload to send after the command byte
        
        reply_length:
        How many bytes to expect as a reply
        """
        
        frame = []
        frame.append(self.get_command_byte(command, address))
        frame += payload
        return self.send_frame(frame, reply_length=reply_length)
    
    def send_bitmap_data_led(self, address, bitmap_data):
        """
        Send bitmap data to an LED display.
        
        address:
        The bus address of the display (0x00 ... 0x0F)
        
        bitmap_data:
        The bitmap data in MONO LED format:
        - 8-bit columns
        - bottom-most column first
        - LSB topmost in column
        - Left to right
        """
        
        payload = [0xFF, len(bitmap_data)] + bitmap_data
        payload.append(self.checksum_led(bitmap_data))
        return self.send_command(address, self.CMD_BITMAP_DATA_LED, payload)
    
    def send_image_led(self, address, image):
        """
        Send an image to an LED display.
        
        address:
        The bus address of the display (0x00 ... 0x0F)
        
        image:
        Either a path to an image file or a PIL Image object.
        White pixels will be on, black pixels will be off.
        """
        
        if not _HAS_PIL:
            raise RuntimeError("The PIL / Pillow module is not installed. It is required for sending image files over MONO.")
        
        if type(image) is str:
            image = Image.open(image)
        elif type(image) is not Image:
            raise ValueError("image needs to be either a file path or a PIL Image instance")
        
        pixels = image.load()
        width, height = image.size
        max_col_end = math.ceil(height / 8) * 8
        img_data = []
        for x in range(width):
            for col_start in range(max_col_end-8, -1, -8):
                col_byte = 0x00
                for y in range(col_start, col_start+8):
                    col_byte |= (pixels[x, y] > 0) << (y%8)
                img_data.append(col_byte)
        return self.send_bitmap_data_led(address, img_data)
    
    def display_image_led(self, address, image):
        """
        Display an image on an LED display.
        Compared to send_image_led, this also sends all required
        pre and post commands to actually update the display.
        
        address:
        The bus address of the display (0x00 ... 0x0F)
        
        image:
        Either a path to an image file or a PIL Image object.
        White pixels will be on, black pixels will be off.
        """
        
        attributes = self.connected_displays.get(address)
        if attributes is None:
            raise RuntimeError("Display attributes are not set for address {}".format(address))
        
        width = attributes.get('width')
        height = attributes.get('height')
        num_img_bytes = width * math.ceil(height/8)
        width_blocks = math.ceil(width/4)
        height_blocks = math.ceil(height/4)
        
        self.send_command(address, self.CMD_PRE_BITMAP_LED_1, [0x00, 0xff, 0x2f, 0x10, 0x20, 0x40, 0x60, 0x90, 0xc0, 0xf0, 0x03, 0x13, 0x33, 0x53, 0x83, 0xb3, 0xe3, 0x89])
        time.sleep(0.05)
        self.send_command(address, self.CMD_PRE_BITMAP_LED_2, [0x01, 0x00, 0x00, 0x00, 0x00, 0x00, num_img_bytes, width_blocks, height_blocks])
        time.sleep(0.05)
        self.send_image_led(address, image)
        time.sleep(0.05)
        self.send_command(address, self.CMD_DISPLAY_BITMAP_LED, [0x1a])
        time.sleep(0.05)
    
    def send_column_data_flipdot(self, address, col_address, column_data):
        """
        Send column data to a flipdot display.
        
        address:
        The bus address of the display (0x00 ... 0x0F)
        
        col_address:
        The address of the column (left to right)
        
        column_data:
        The column data in MONO flipdot format:
        - 4 pixels per byte, appropriate number of bytes per column
        - First byte: topmost pixels
        - Bit order per byte:
            - Bit 7: topmost pixel enable (1=flip, 0=skip)
            - Bit 6: topmost pixel color (1=yellow, 0=black)
            - Bits 5 to 0 are the same for the other 3 pixels
        """
        
        payload = [col_address] + column_data + [0x00]
        payload.append(self.checksum_flipdot([self.get_command_byte(self.CMD_COLUMN_DATA_FLIPDOT, address)] + payload))
        return self.send_command(address, self.CMD_COLUMN_DATA_FLIPDOT, payload)
    
    def send_image_flipdot(self, address, image, col_offset):
        """
        Send an image to a flipdot display.
        
        address:
        The bus address of the display (0x00 ... 0x0F)
        
        image:
        Either a path to an image file or a PIL Image object.
        White pixels will be on, black pixels will be off.
        
        col_offset:
        The column address offset, i.e. the address of the leftmost column
        """
        
        if not _HAS_PIL:
            raise RuntimeError("The PIL / Pillow module is not installed. It is required for sending image files over MONO.")
        
        if type(image) is str:
            image = Image.open(image)
        elif not isinstance(image, Image.Image):
            raise ValueError("image needs to be either a file path or a PIL Image instance")
        
        pixels = image.convert('L').load()
        width, height = image.size
        max_col_end = math.ceil(height / 4) * 4
        col_addr = col_offset
        for x in range(width):
            col_data = []
            for col_start in range(max_col_end-4, -1, -4):
                col_byte = 0b10101010 # Default: all pixels flipped, none skipped
                for y in range(col_start, col_start+4):
                    col_byte |= (pixels[x, height-y-1] > 0) << (6-((y%4)*2))
                col_data.append(col_byte)
            self.send_column_data_flipdot(address, col_addr, col_data)
            col_addr += 1
            if x != 0 and (x+1) % 28 == 0:
                col_addr += 4
            time.sleep(0.02)
    
    def display_image_flipdot(self, address, image, col_offset):
        """
        Display an image on a flipdot display.
        Compared to send_image_flipdot, this also sends all required
        pre and post commands to actually update the display.
        
        address:
        The bus address of the display (0x00 ... 0x0F)
        
        image:
        Either a path to an image file or a PIL Image object.
        White pixels will be on, black pixels will be off.
        
        col_offset:
        The column address offset, i.e. the address of the leftmost column
        """
        
        self.send_command(address, self.CMD_PRE_BITMAP_FLIPDOT, [0x00, 0x10, 0x00, 0x50, 0x00, 0x02, 0x2E])
        time.sleep(0.05)
        self.send_image_flipdot(address, image, col_offset)
