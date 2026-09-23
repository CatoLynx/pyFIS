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


class DummyGpioBackend(BaseGpioBackend):
    def __init__(self, debug = False):
        self.debug = debug

    def setup_channel(self, channel, mode, pull=None):
        if self.debug:
            print(f"DummyGPIO: Setting channel {channel} to mode {mode} with pull {pull}")

    def clean_up(self):
        if self.debug:
            print("DummyGPIO: Cleaning up")

    def set_output(self, channel, state):
        if self.debug:
            print(f"DummyGPIO: Setting channel {channel} to state {state}")

    def get_input(self, channel):
        if self.debug:
            print(f"DummyGPIO: Getting channel {channel} (returning LOW)")
        return self.STATE_LOW
