"""
Copyright 2019 - 2023 Julian Metzler

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

from .exceptions import CommunicationError
from ..utils.base_serial import BaseSerialPort


class Krone8200Display:
    """
    Controls split-flap displays using the Krone 8200 system.
    This can be used to control an entire Krone 8200 platform display
    without any modifications.
    """

    STX = 0x02
    ETX = 0x03
    EOT = 0x04
    ENQ = 0x05
    DLE = 0x10
    NAK = 0x15
    ETB = 0x17
    PAD = 0x7F
    ACK0 = (DLE, 0x30)
    ACK1 = (DLE, 0x31)
    WABT = (DLE, 0x3F)

    SIDE_BOTH = 0
    SIDE_A = 1
    SIDE_B = 2

    DEBUG_CHARS = {
        STX: "STX",
        ETX: "ETX",
        EOT: "EOT",
        ENQ: "ENQ",
        DLE: "DLE",
        NAK: "NAK",
        ETB: "ETB",
        PAD: "PAD"
    }

    def __init__(self, port, address, debug = False, exclusive = True):
        self.debug = debug
        if isinstance(port, serial.Serial) or isinstance(port, BaseSerialPort):
            self.port = port
        else:
            self.port = serial.Serial(port, baudrate=2400, timeout=1.0, exclusive=exclusive)
        # To enable receiving responses (DTR coupled to Rx via optocoupler)
        self.port.setDTR(1)
        # Set Rx address
        self.rx_address = address
        # Tx address is 1 byte less
        self.tx_address = (address[0]-1, address[1]-1)

    def make_parity(self, byte):
        result = byte
        num_ones = 0
        for n in range(8):
            if (byte >> n) & 1:
                num_ones += 1
        if num_ones % 2 != 0:
            result |= 0x80
        else:
            result &= 0x7F
        return result

    def make_lrc(self, data):
        lrc = 0x7F
        for b in data:
            lrc ^= b
        return lrc

    def debug_message(self, message):
        """
        Turn a message into a readable form
        """
        result = ""
        for byte in message:
            byte &= 0x7F
            if byte in self.DEBUG_CHARS:
                result += self.DEBUG_CHARS[byte]
            elif byte in range(0, 32) or byte == 127:
                result += "<{:02X}>".format(byte)
            else:
                result += chr(byte)
            result += " "
        return result

    def read_response(self):
        """
        Read the response from the addressed station
        """
        timeout = 0.0
        while not self.port.inWaiting():
            time.sleep(0.1)
            timeout += 0.1
            if timeout >= 3.0:
                raise CommunicationError("No response received from display")
        response = self.port.read(self.port.inWaiting())

        while True:
            time.sleep(0.1)
            in_waiting = self.port.inWaiting()
            if not in_waiting:
                break
            response += self.port.read(in_waiting)

        if self.debug:
            print("RX: " + self.debug_message(response))

        if not response:
            raise CommunicationError("No response received from display")

        response = [byte & 0x7F for byte in response] # Strip checksum bit; TODO: Actually check it

        if response[0] != self.PAD:
            raise CommunicationError("First byte of response should be PAD, was " + self.debug_message(response[0:1]))

        if len(response) >= 2 and response[1] == self.NAK:
            raise CommunicationError("NAK response")

        return response[1:] # Strip leading PAD

    def read_response_and_handle_wait(self, tx=False):
        response = self.read_response()
        wait_count = 0
        while self.check_response_wait(response):
            wait_count += 1
            if wait_count >= 3:
                self.send_end_comm()
                raise CommunicationError("Maximum wait retries exceeded")
            time.sleep(3)
            if tx:
                self.send_raw_message([self.PAD, self.EOT, self.PAD, self.tx_address[0], self.tx_address[1], self.ENQ, self.PAD])
            else:
                self.send_raw_message([self.PAD, self.EOT, self.PAD, self.rx_address[0], self.rx_address[1], self.ENQ, self.PAD])
            response = self.read_response()
        return response

    def send_raw_message(self, message):
        for i, byte in enumerate(message):
            message[i] = self.make_parity(byte)
        if self.debug:
            print("TX: " + self.debug_message(message))
        self.port.write(bytearray(message))

    def send_rx_request(self):
        self.send_raw_message([self.PAD, self.EOT, self.PAD, self.rx_address[0], self.rx_address[1], self.ENQ, self.PAD])
        time.sleep(0.2)
        response = self.read_response_and_handle_wait(tx=False)
        return self.check_response_ack(response)

    def send_tx_request(self):
        self.send_raw_message([self.PAD, self.EOT, self.PAD, self.tx_address[0], self.tx_address[1], self.ENQ, self.PAD])
        time.sleep(0.5)
        response = self.read_response_and_handle_wait(tx=True)
        return response

    def check_response_wait(self, response):
        # Return True if the response is a "wait" sequence
        if tuple(response) == self.WABT:
            return True
        return False

    def check_response_ack(self, response):
        if tuple(response) not in (self.ACK0, self.ACK1):
            return False
        return True

    def send_message(self, message):
        """
        Send a message. Requires the station to be addressed with send_comm_request before.
        """
        data = [self.STX] + list(map(ord, message)) + [self.ETX]
        cmd = [self.PAD] + data
        cmd.append(self.make_lrc(data[1:]))
        cmd.append(self.PAD)
        self.send_raw_message(cmd)

    def send_end_comm(self):
        self.send_raw_message([self.PAD, self.EOT, self.PAD])

    def send_ack0(self):
        self.send_raw_message([self.PAD, self.DLE, 0x30, self.PAD])

    def send_command(self, address, side, command):
        """
        Send a simple command
        """
        if not self.send_rx_request():
            return False
        self.send_message("{address:>02}{side:>01}{command}".format(address=address, side=side, command=command))
        time.sleep(0.2)

        response = self.read_response_and_handle_wait(tx=False)
        if not self.check_response_ack(response):
            return False
        self.send_end_comm()
        return True

    def send_command_with_response(self, address, side, command):
        """
        Send a command and retrieve the response data
        """
        if not self.send_command(address, side, command):
            return None
        return self.send_tx_request()

    def set_home(self, address = 1, side = 0):
        """
        Set all units to their home position
        """
        return self.send_command(address, side, "R")

    def set_positions(self, positions, auto_update = True, address = 1, side = 0):
        """
        Set all units with sequential addressing
        positions: list of positions for units starting at address 1
        """
        command = "C" + "".join(["{:>02}".format(p) for p in positions])
        if auto_update:
            command += "@A"
        return self.send_command(address, side, command)

    def set_positions_addressed(self, positions, auto_update = True, address = 1, side = 0):
        """
        Set all units with explicit addressing
        positions: dict of format {address: position}
        """
        command = "E" + "".join(["{a:>02}{p:>02}".format(a=a, p=p) for a, p in positions.items()])
        if auto_update:
            command += "@A"
        return self.send_command(address, side, command)

    def update(self, address = 1, side = 0):
        """
        Update units (cause them to actually turn)
        """
        return self.send_command(address, side, "A")

    def set_light(self, unit, state, auto_update = True, address = 1, side = 0):
        """
        Set backlight (if supported)
        unit: unit address which controls the light
        state: 1 or 0
        """
        command = "Z{:02d}{:02d}".format(unit, state)
        if auto_update:
            command += "@A"
        return self.send_command(address, side, command)

    def set_blinker(self, unit, state, auto_update = True, address = 1, side = 0):
        """
        Set blinker (if supported)
        unit: unit address which controls the blinkers
        state: 0 (lights off), 1 (light 1 on), 2 (light 2 on), 3 (both lights on)
        Needs to be followed by a set_light command
        """
        command = "B{:02d}{:02d}".format(unit, state)
        if auto_update:
            command += "@A"
        return self.send_command(address, side, command)

    def restart(self, address = 1, side = 0):
        """
        Restart the controller
        """
        return self.send_command(address, side, "Y")

    def lock_units(self, units, address = 1, side = 0):
        """
        Lock the specified units (cause them to ignore input)
        units: unit addresses to be locked
        """
        command = "S" + "".join(["{:>02}".format(u) for u in units])
        return self.send_command(address, side, command)

    def unlock_units(self, units, address = 1, side = 0):
        """
        Unlock the specified units (cause them to accept input)
        units: unit addresses to be unlocked
        """
        command = "F" + "".join(["{:>02}".format(u) for u in units])
        return self.send_command(address, side, command)

    def read_status(self, units, address = 1, side = 0):
        """
        Read the status of the specified units.
        units: unit addresses to be read
        """
        command = "M" + "".join(["{:>02}".format(u) for u in units])
        return self.send_command_with_response(address, side, command)

    def read_positions(self, units, address = 1, side = 0):
        """
        Read the positions of the specified units.
        units: unit addresses to be read
        """
        command = "L" + "".join(["{:>02}".format(u) for u in units])
        return self.send_command_with_response(address, side, command)

    def d_set_module_data(self, module_data):
        # Compatibility function for SplitFlapDisplay class
        # TODO: Handle side and address?
        self.set_positions_addressed(dict(module_data), auto_update=True)

    def d_update(self):
        # Compatibility function for SplitFlapDisplay class
        pass
