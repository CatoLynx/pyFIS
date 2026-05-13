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

import socket
import time


class VistraITCPBackend:
    """
    TCP/IP backend for VISTRA-I
    """
    
    def __init__(self, hostname, port, timeout = 5.0):
        """
        hostname:
        The network hostname of the display to connect to
        
        port:
        The TCP port to use for communication
        
        timeout:
        Timeout for socket connection in seconds
        """
        
        self.hostname = hostname
        self.port = port
        self.timeout = timeout
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
    
    def send_raw_message(self, message):
        """
        Send a raw message to the display.
        
        message:
        The message as a bytestring
        """
        
        # Renew socket if necessary
        if time.time() - self.last_transmission > 300: # 5 minutes
            self.renew_socket()
        
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
