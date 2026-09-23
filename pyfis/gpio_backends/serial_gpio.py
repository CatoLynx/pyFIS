"""
Copyright 2026 Julian Metzler

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

from .base_gpio import BaseGpioBackend


class SerialGpioBackend(BaseGpioBackend):
    """
    Backend that uses the RTS or DTR pin.
    Channel 0 = RTS, channel 1 = DTR
    """

    def __init__(self, device, debug = False):
        self.device = device
        self.debug = debug

    def setup_channel(self, channel, mode, pull=None):
        if self.debug:
            print(f"SerialGPIO: Ignoring channel setup request (only outputs without pull resistors available)")

    def clean_up(self):
        if self.debug:
            print("SerialGPIO: Cleaning up (nothing to do)")

    def set_output(self, channel, state):
        if self.debug:
            print(f"SerialGPIO: Setting channel {channel} to state {state}")
        if channel == 0:
            self.device.setRTS(not state)
        elif channel == 1:
            self.device.setDTR(not state)

    def get_input(self, channel):
        if self.debug:
            print(f"SerialGPIO: Ignoring channel get request (only outputs without pull resistors available) (returning LOW)")
        return self.STATE_LOW
