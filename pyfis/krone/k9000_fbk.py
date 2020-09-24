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

from itertools import groupby

from .k9000_rs485 import Krone9000RS485Controller
from .exceptions import CommunicationError


class Krone9000FBK(Krone9000RS485Controller):
    """
    Controls a FBK (Fallblatt-Buskopfkarte)
    (split-flap group control) board.
    """
    
    BOARD_ID = 0xB2
    BOARD_NAME = "FBK"
    
    FLAG_START_IMMEDIATELY = 0x80
    FLAG_FBM_COMMAND = 0x40
    FLAG_ENABLE_COMPRESSION = 0x20
    
    CMD_GET_FBK_STATUS = 0x01
    CMD_GET_LINE_INIT_DATA = 0x02
    CMD_GET_LINE_DATA = 0x03
    CMD_SET_BLINKER = 0x0B
    CMD_SET_FBM_VALUE_TABLE = 0x0E
    CMD_LOCK_FBK = 0xC6
    CMD_UNLOCK_FBK = 0xC7
    
    CMD_FBM_START = 0x00 | FLAG_START_IMMEDIATELY
    CMD_GET_FBM_STATUS = 0x03 | FLAG_FBM_COMMAND
    CMD_GET_FBM_CONTENT = 0x04 | FLAG_FBM_COMMAND
    CMD_CLEAR_FBM = 0x05 | FLAG_FBM_COMMAND
    CMD_LOCK_FBM = 0x06 | FLAG_FBM_COMMAND | FLAG_START_IMMEDIATELY
    CMD_UNLOCK_FBM = 0x07 | FLAG_FBM_COMMAND | FLAG_START_IMMEDIATELY
    CMD_SET_FBM_CODES_SEQ = 0x08 | FLAG_FBM_COMMAND
    CMD_SET_FBM_CODES_ADDR = 0x09 | FLAG_FBM_COMMAND
    
    def _get_fbm_status(self, stat):
        # Return human-readable error strings
        # based on FBM error bits
        if stat & 0x08:
            lut = {
                0b1000: "comm_error",
                0b1001: "start_missing",
                0b1010: "unknown_char",
                0b1011: "external_rotation",
                0b1100: "rotation_timeout",
                0b1101: "fbm_missing",
                0b1111: "rotating"
            }
            return [lut.get(stat & 0x0f, "")]
        else:
            errors = []
            if stat & 0x04:
                errors.append("no_ac")
            if stat & 0x02:
                errors.append("no_flap_imps")
            if stat & 0x01:
                errors.append("no_home_imp")
            return errors
    
    def _rle(self, data):
        # Simple run-length encoding
        rle_data = []
        for k,i in groupby(data):
            run = list(i)
            if(len(run) > 2):
                while len(run) > 128:
                    rle_data.extend([(len(run) - 1) | 0x80, k])
                    run = run[128:]
                rle_data.extend([(len(run) - 1) | 0x80, k])
            else:
                rle_data.extend(run)
        return rle_data
    
    def get_status(self):
        # Get the status of the FBK board
        payload = self.send_command(self.CMD_GET_FBK_STATUS, response=True)
        stat = payload[1]
        status = {
            'comm_err': bool(stat & 0x40),
            'reset': bool(stat & 0x20),
            'locked': bool(stat & 0x10),
            'fbm_err': bool(stat & 0x08),
            'blinker_err': bool(stat & 0x04),
            'fbm_start_missing': bool(stat & 0x02),
            'sw_ver': f"{payload[2]}.{payload[3]}"
        }
        return status
    
    def get_fbm_ids(self):
        # Get a list of all connected FBM IDs
        payload = self.send_command(self.CMD_GET_LINE_INIT_DATA, response=True)
        module_data = payload[1:]
        modules_present = []
        addr = 0
        for byte in module_data:
            for bit in range(7):
                if byte & (1 << bit):
                    modules_present.append(addr)
                addr += 1
                if addr > 255:
                    break
        return modules_present
    
    def get_fbm_statuses(self):
        # True means okay, False means FBM error or not present
        # (see get_fbm_ids to get a list of present FBMs)
        payload = self.send_command(self.CMD_GET_LINE_DATA, response=True)
        module_data = payload[1:]
        module_statuses = {}
        addr = 0
        for byte in module_data:
            for bit in range(7):
                module_statuses[addr] = bool(byte & (1 << bit))
                addr += 1
                if addr > 255:
                    break
        return module_statuses
    
    def set_blinker(self, state):
        # Set the blinker associated with this FBK on or off
        return self.send_command(self.CMD_SET_BLINKER, 0x31 if state else 0x30)
    
    def set_fbm_value_table(self, addr, table):
        # Set the internal mapping of character code to flap position
        # on the selected FBM
        # table is a list of characters to be mapped to flaps,
        # starting at flap 0
        parameters = [addr] + table
        self.send_command(self.CMD_SET_FBM_VALUE_TABLE, parameters)
        # Special case here: The FBK sends the number of flap codes transferred
        # as a single byte after it has finished sending the data to the FBM.
        # As this is the only case in which this sort of response occurs,
        # we are just handling it manually here.
        num_xferred = b""
        tries = 0
        # Try for roughly five seconds (exact value depends on the port timeout)
        while num_xferred == b"":
            if tries >= 5.0 / self.port.timeout:
                raise CommunicationError("Timeout while waiting for result of FBM value table transfer")
            num_xferred = self.port.read(1)
            tries += 1
        self.debug_print(bytearray(num_xferred), receive=True)
        # Return the number of transferred flap codes
        return ord(num_xferred)
    
    def lock(self):
        # Lock the entire FBK
        return self.send_command(self.CMD_LOCK_FBK)
    
    def unlock(self):
        # Unlock the entire FBK
        return self.send_command(self.CMD_UNLOCK_FBK)
    
    def start_fbm(self):
        return self.send_command(self.CMD_FBM_START)
    
    def get_detailed_fbm_statuses(self, addrs):
        # Get detailed FBM status information for up to 10 FBMs.
        # addrs is a list of FBM IDs to be queried
        payload = self.send_command(self.CMD_GET_FBM_STATUS, addrs, response=True)
        module_statuses = {}
        data = payload[1:]
        for i in range(0, len(data), 2):
            addr = data[i]
            stat = data[i + 1]
            module_statuses[addr] = {
                'home_pos': bool(stat & 0x40),
                'reset': bool(stat & 0x20),
                'locked': bool(stat & 0x10),
                'status': self._get_fbm_status(stat & 0x0f)
            }
        return module_statuses
    
    def get_all_detailed_fbm_statuses(self):
        # Automatically read the list of connected FBM IDs
        # and query all of them for detailed status information
        module_statuses = {}
        for addrs in self._chunks(self.get_fbm_ids(), 10):
            module_statuses.update(self.get_detailed_fbm_statuses(addrs))
        return module_statuses
    
    def get_fbm_contents(self, addrs):
        # Get the currently displayed character for up to 10 FBMs.
        # addrs is a list of FBM IDs to be queried
        payload = self.send_command(self.CMD_GET_FBM_CONTENT, addrs, response=True)
        module_contents = {}
        data = payload[1:]
        for i in range(0, len(data), 2):
            addr = data[i]
            char = data[i + 1]
            module_contents[addr] = chr(char)
        return module_contents
    
    def get_all_fbm_contents(self):
        # Automatically read the list of connected FBM IDs
        # and query all of them for their content
        module_contents = {}
        for addrs in self._chunks(self.get_fbm_ids(), 10):
            module_contents.update(self.get_fbm_contents(addrs))
        return module_contents
    
    def clear_fbm(self, addrs = None, immediate = True):
        # Clear all or the selected FBMs
        cmd = self.CMD_CLEAR_FBM
        if immediate:
            cmd |= self.FLAG_START_IMMEDIATELY
        return self.send_command(cmd, addrs)
    
    def lock_fbm(self, addrs = None):
        # Lock all or the selected FBMs
        return self.send_command(self.CMD_LOCK_FBM, addrs)
    
    def unlock_fbm(self, addrs = None):
        # Unlock all or the selected FBMs
        return self.send_command(self.CMD_UNLOCK_FBM, addrs)
    
    def set_fbm_codes_seq(self, codes, immediate = False, compress = False):
        # Set FBM character codes to be displayed
        # sequentially (without explicit addressing)
        cmd = self.CMD_SET_FBM_CODES_SEQ
        if immediate:
            cmd |= self.FLAG_START_IMMEDIATELY
        if compress:
            cmd |= self.FLAG_ENABLE_COMPRESSION
            codes = self._rle(codes)
        return self.send_command(cmd, codes)
    
    def set_fbm_codes_addr(self, codes, immediate = False):
        # Set FBM character codes to be displayed
        # with explicit addressing
        cmd = self.CMD_SET_FBM_CODES_ADDR
        if immediate:
            cmd |= self.FLAG_START_IMMEDIATELY
        return self.send_command(cmd, codes)
    
    def d_set_module_data(self, module_data):
        # Compatibility function for SplitFlapDisplay class
        for chunk in self._chunks(module_data, 50):
            self.set_fbm_codes_addr([i for s in chunk for i in s])
    
    def d_update(self):
        # Compatibility function for SplitFlapDisplay class
        self.start_fbm()
