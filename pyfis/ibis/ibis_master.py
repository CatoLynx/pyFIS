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

from .ibis_protocol import IBISProtocol
from ..utils.serial import ensure_serial_port


class IBISMaster(IBISProtocol):
    """
    An IBIS bus master, sending and receiving telegrams. Defaults to serial port backend.
    """
    
    def __init__(self, port, baudrate = 1200, bytesize = 7, parity = 'E',
                 stopbits = 2, timeout = 2.0, exclusive = True, *args, **kwargs):
        """
        port:
        The serial port to use for communication
        """
        
        super().__init__(*args, **kwargs)
        self.device = ensure_serial_port(port,
            baudrate = baudrate,
            bytesize = bytesize,
            parity = parity,
            stopbits = stopbits,
            timeout = timeout,
            exclusive=exclusive)
    
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
