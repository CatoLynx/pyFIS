"""
Copyright (C) 2026 Julian Metzler

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

import time

from ..utils.serial import ensure_serial_port


class VistraISerialBackend:
    """
    Serial backend for VISTRA-I
    """
    
    def __init__(self, port, baudrate = 115200, bytesize = 8, parity = 'N', stopbits = 1, timeout = 5.0, exclusive = True):
        """
        port:
        The serial port to use for communication
        """
        
        self.device = ensure_serial_port(port,
            baudrate = baudrate,
            bytesize = bytesize,
            parity = parity,
            stopbits = stopbits,
            timeout = timeout,
            exclusive=exclusive)
    
    def send_raw_message(self, message):
        """
        Send a raw message to the display.
        
        message:
        The message as a bytestring
        """
        
        try:
            #print(message)
            self.device.write(message)
            # Receive up until the "RequestedDataType" byte
            reply = bytearray(self.device.read(9))
            #print(reply)
            data_type = reply[8]
            if data_type != 0x00:
                # Receive data length
                reply += bytearray(self.device.read(4))
                length = (
                    (reply[12] << 24)
                    | (reply[11] << 16)
                    | (reply[10] << 8)
                    | reply[9])
                # Receive the rest of the data
                reply += bytearray(self.device.read(length+1)) # +1 for end byte
            else:
                # Receive end byte
                reply += bytearray(self.device.read(1))
            return reply
        except IndexError:
            # Not enough data received
            raise TimeoutError("Not enough data received from display")
