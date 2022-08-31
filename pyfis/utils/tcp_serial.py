"""
Copyright (C) 2022 Julian Metzler

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


class TcpSerialPort:
    def __init__(self, host, port, timeout=2.0):
        """
        host: The hostname or IP to connect to
        port: The TCP port to use for communication
        timeout: The socket timeout in seconds
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.socket.settimeout(timeout)
    
    def write(self, data):
        return self.socket.send(bytearray(data))
    
    def read(self, length):
        # Read the specified number of bytes, blocking
        return self.socket.recv(length)

    def setRTS(self, state):
        pass

    def setDTR(self, state):
        pass

    def getCTS(self):
        return 0

    def getDSR(self):
        return 0

    def getRI(self):
        return 0

    def getCD(self):
        return 0

    def __del__(self):
        self.socket.close()