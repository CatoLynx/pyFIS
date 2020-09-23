"""
Copyright (C) 2019 - 2020 Julian Metzler

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

from .exceptions import CommunicationError, NACKError, BusyError


class Krone9000RS485Controller:
    """
    Basic control scheme for the internal RS485 bus
    in the KRONE 9000 system.
    """
    
    FLAG_ACK = 0x80
    
    CTRL_READ = 0x01
    CTRL_WRITE_SINGLE = 0x02
    CTRL_WRITE_BLOCK = 0x04
    
    STATUS_ACK = 0x06
    STATUS_BUSY = 0x10
    STATUS_NACK = 0x15
    
    MAX_CHUNK_SIZE = 128
    RETRY_COUNT = 10
    RETRY_INTERVAL = 0.2

    def __init__(self, port, address, timeout = 1.0, debug = False, exclusive = False):
        self.address = address
        self.debug = debug
        if isinstance(port, serial.Serial):
            self.port = port
        else:
            self.port = serial.Serial(port, baudrate=19200, timeout=timeout, exclusive=exclusive)
    
    @staticmethod
    def _chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    
    def debug_print(self, data, receive = False):
        if self.debug:
            print(f"{self.BOARD_NAME:<4} {self.address} {'RX' if receive else 'TX'}: " + " ".join((format(x, "02X") for x in data)))
    
    def make_checksum(self, payload):
        checksum = 0x00
        for byte in payload:
            checksum ^= byte
        return checksum
    
    def check_checksum(self, data):
        checksum = self.make_checksum(data[2:-1])
        return checksum == data[-1]
            
    def send_command(self, command, parameters = None, response = False, ack = True, block = False):
        def _chunks(lst, n):
            # Yield successive n-sized chunks from lst.
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
        
        data = [command]
        if parameters is not None:
            if type(parameters) in (list, tuple):
                data.extend(parameters)
            else:
                data.append(parameters)
        
        if len(data) > self.MAX_CHUNK_SIZE and block == False:
            raise CommunicationError("Data too long for single-block transfer. Use multi-block mode!")
        
        if response:
            control = self.CTRL_READ
        else:
            if block:
                control = self.CTRL_WRITE_BLOCK
            else:
                control = self.CTRL_WRITE_SINGLE
        
        if ack:
            control |= self.FLAG_ACK
        
        for chunk_id, chunk in enumerate(_chunks(data, self.MAX_CHUNK_SIZE)):
            for retry in range(self.RETRY_COUNT):
                payload = [self.BOARD_ID, self.address, 0x00, control, chunk_id + 1] + chunk + [0x00]
                length = len(payload)
                payload[2] = length
                checksum = self.make_checksum(payload)
                cmd_bytes = [0xFF, 0xFF] + payload + [checksum]
                
                # Debug output if enabled
                self.debug_print(cmd_bytes)
                
                # Send it
                self.port.write(bytearray(cmd_bytes))
                
                # Check status
                if not response:
                    if control & self.FLAG_ACK:
                        try:
                            self.check_status()
                        except BusyError:
                            if retry >= self.RETRY_COUNT - 1:
                                raise
                            else:
                                time.sleep(self.RETRY_INTERVAL)
                        else:
                            break
                else:
                    break

        # Read response
        if response:
            return self.read_response()
        else:
            return None
    
    def check_status(self):
        status = bytearray(self.port.read(1))[0]
        self.debug_print([status], receive=True)
        if status == self.STATUS_ACK:
            return True
        elif status == self.STATUS_BUSY:
            raise BusyError()
        elif status == self.STATUS_NACK:
            raise NACKError()
        else:
            raise CommunicationError(f"Unknown status byte {status:02X}")
    
    def read_response(self):
        data = bytearray()
        header = bytearray(self.port.read(4))
        if len(header) != 4:
            if len(header) == 1:
                if header[0] == self.STATUS_BUSY:
                    raise BusyError()
                if header[0] == self.STATUS_NACK:
                    raise NACKError()
            header_fmt = " ".join((format(x, "02X") for x in header))
            raise CommunicationError(f"Incomplete header: {header_fmt}")
        if header[0] != 0xFF or header[1] != 0xFF:
            raise CommunicationError(f"Invalid start sequence {header[0]:02X} {header[1]:02X}")
        if header[2] != self.BOARD_ID:
            raise CommunicationError(f"Invalid board ID {header[2]:02X}")
        if header[3] != self.address:
            raise CommunicationError(f"Invalid address {header[3]:02X}")
        data.extend(header)
        
        length = bytearray(self.port.read(1))[0]
        payload = bytearray(self.port.read(length - 3))
        checksum = bytearray(self.port.read(1))[0]
        
        data.append(length)
        data.extend(payload)
        data.append(checksum)
        
        self.debug_print(data, receive=True)
        if not self.check_checksum(data):
            raise CommunicationError("Checksum mismatch")
        return payload[2:-1]
    
    def send_heartbeat(self):
        cmd_bytes = [0xFF, 0xFF, self.BOARD_ID, self.address, 0x00]
        self.debug_print(cmd_bytes)
        self.port.write(bytearray(cmd_bytes))