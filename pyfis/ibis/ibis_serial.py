"""
Copyright (C) 2016 - 2020 Julian Metzler

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

from .ibis_protocol import IBISProtocol

class SerialIBISMaster(IBISProtocol):
    """
    An IBIS bus master, sending and receiving telegrams using a serial port
    """
    
    def __init__(self, port, baudrate = 1200, bytesize = 7, parity = 'E',
                 stopbits = 2, timeout = 2.0, exclusive = False, *args, **kwargs):
        """
        port:
        The serial port to use for communication
        """
        
        super().__init__(*args, **kwargs)
        
        if isinstance(port, serial.Serial):
            self.device = port
            self.port = self.device.port
        else:
            self.port = port
            self.device = serial.Serial(
                self.port,
                baudrate = baudrate,
                bytesize = bytesize,
                parity = parity,
                stopbits = stopbits,
                timeout = timeout,
                exclusive=exclusive
            )
    
    def _send(self, telegram):
        """
        Actually send the telegram.
        This varies depending on implementation
        """
        
        self.device.write(telegram)
    
    def _receive(self, length):
        """
        Actually receive data.
        This varies depending on implementation and needs to be overridden
        """
        
        return self.device.read(length)

    def __del__(self):
        self.device.close()
