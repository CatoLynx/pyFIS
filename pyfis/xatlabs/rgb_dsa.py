"""
Copyright (C) 2021 Julian Metzler

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

from pprint import pprint


from .exceptions import CommunicationError


class xatLabsRGBDSAController:
    """
    Protocol implementation for a custom built replacement
    for the ubiquitous orange LED signs in DB stations.
    Uses 8x8 WS2812 matrix boards and an Arduino-based controller.
    Custom serial protocol is implemented here.
    """

    CMD_SET_TEXT = 0xA0
    CMD_SET_BRIGHTNESS = 0xA1
    CMD_DELETE_TEXT = 0xA2

    SYNC = 0xCC

    ERR_TIMEOUT = 0xE0
    ERR_UNKNOWN_CMD = 0xE1
    ERR_PAYLOAD_TOO_LARGE = 0xE2
    ERR_GENERIC = 0xEE

    SUCCESS = 0xFF

    NO_CLEAR     = 0b00001000

    ALIGN_LEFT   = 0b00000100
    ALIGN_CENTER = 0b00000110
    ALIGN_RIGHT  = 0b00000010

    SCROLL       = 0b00000001

    def __init__(self, port, debug = False, exclusive = True, no_dtr = False):
        self.debug = debug
        if isinstance(port, serial.Serial):
            self.port = port
        else:
            self.port = serial.Serial()
            self.port.port = port
            self.port.baudrate = 115200
            self.port.timeout = 2.0
            self.port.exclusive = exclusive
            if no_dtr:
                self.port.setDTR(False)
            self.port.open()

    def debug_message(self, message):
        """
        Turn a message into a readable form
        """
        result = ""
        for byte in message:
            if True or byte in range(0, 32) or byte >= 127:
                result += "{:02X}".format(byte)
            else:
                result += chr(byte)
            result += " "
        return result

    def sync(self):
        """
        Wait for a sync byte from the serial port
        """
        # Flush buffer first since we must not read old sync bytes
        self.port.read(self.port.inWaiting())
        sync = None
        while not sync:
            if self.debug:
                print("Syncing")
            sync = self.port.read(1)
        if self.debug:
            print("Synced")
        if sync[0] == self.SYNC:
            return True
        else:
            raise CommunicationError("Sync: Unexpected byte 0x{:02X}".format(sync[0]))

    def read_response(self):
        """
        Read the response
        """
        response = [self.SYNC]
        while response and response[0] == self.SYNC:
            response = self.port.read(1)
        if not response:
            raise CommunicationError("Timeout (no response)")
        if self.debug:
            print("RX: " + self.debug_message(response))
        if response[0] == self.ERR_TIMEOUT:
            raise CommunicationError("Timeout (device received incomplete message)")
        if response[0] == self.ERR_UNKNOWN_CMD:
            raise CommunicationError("Unknown command")
        if response[0] == self.ERR_PAYLOAD_TOO_LARGE:
            raise CommunicationError("Payload too large")
        if response[0] == self.ERR_GENERIC:
            raise CommunicationError("Generic error")
        if response[0] == self.SUCCESS:
            return True
        return False

    def send_command(self, action, payload):
        data = [0xFF, action] + payload
        if self.debug:
            print("TX: " + self.debug_message(data))
        self.port.write(bytearray(data))

    def send_command_with_response(self, action, payload):
        """
        Send a command and retrieve the response data
        """
        self.send_command(action, payload)
        return self.read_response()

    def set_text(self, slot, text, attrs, duration):
        """
        Set text with color config.

        slot: Which text slot to use
        text: The text to be displayed (either str or list, see below)
        attrs: Combination of attributes (NO_CLEAR, ALIGN, SCROLL)
        duration: Duration for the text to be displayed in ms (Only relevant for non-scrolling texts)

        text list structure:
        [
            {
                "text": "Hello ",
                "color": "ff0000"
            },
            {
                "text": "World!",
                "red": 255,
                "green": 0,
                "blue": 128
            }
        ]
        """
        payload = []

        if type(text) in (list, tuple):
            _text = "".join(d['text'] for d in text).encode("CP437")
            _segments = []
            pos = 0
            for i, t in enumerate(text):
                seg = {}
                seg['start'] = pos
                seg['end'] = pos + len(t['text'])
                if "color" in t:
                    append = True
                    seg['red'] = int(t['color'][0:2], 16)
                    seg['green'] = int(t['color'][2:4], 16)
                    seg['blue'] = int(t['color'][4:6], 16)
                elif "red" in t and "green" in t and "blue" in t:
                    append = True
                    seg['red'] = t['red']
                    seg['green'] = t['green']
                    seg['blue'] = t['blue']
                else:
                    append = False
                if append:
                    _segments.append(seg)
                pos += len(t['text'])
        else:
            _text = str(text).encode("CP437")
            _segments = []

        payload.extend([slot, len(text) >> 8, len(_text) & 0xFF, attrs, duration >> 8, duration & 0xFF])
        payload.extend(_text)
        payload.extend([len(_segments)])
        for seg in _segments:
            payload.extend([0x01, 0x07, seg['start'] >> 8, seg['start'] & 0xFF, seg['end'] >> 8, seg['end'] & 0xFF, seg['red'], seg['green'], seg['blue']])
        payload = [len(payload) >> 8, len(payload) & 0xFF] + payload

        return self.send_command_with_response(self.CMD_SET_TEXT, payload)

    def set_brightness(self, brightness):
        """
        Set display brightness (0 to 255)
        """
        return self.send_command_with_response(self.CMD_SET_BRIGHTNESS, [brightness])

    def delete_text(self, slot):
        """
        Delete the text in the specified slot
        """
        return self.send_command_with_response(self.CMD_DELETE_TEXT, [slot])
