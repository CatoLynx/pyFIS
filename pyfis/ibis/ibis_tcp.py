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

import socket

from .ibis_protocol import IBISProtocol

class TCPIBISMaster(IBISProtocol):
    """
    An IBIS master using TCP instead of serial
    """
    
    def __init__(self, host, port, timeout = 2.0, *args, **kwargs):
        """
        host:
        The hostname or IP to connect to
        
        port:
        The TCP port to use for communication
        
        timeout:
        The socket timeout in seconds
        """
        
        super().__init__(*args, **kwargs)
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.socket.settimeout(timeout)
    
    def _send(self, telegram):
        """
        Actually send the telegram.
        This varies depending on implementation
        """
        
        self.socket.send(telegram)
    
    def _receive(self, length):
        """
        Actually receive data.
        This varies depending on implementation and needs to be overridden
        """
        
        return self.socket.recv(length)

    def __del__(self):
        self.socket.close()