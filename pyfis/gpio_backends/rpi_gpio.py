"""
Copyright 2023 Julian Metzler

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

try:
    import RPi.GPIO as gpio
    HAS_RPI_GPIO = True
except ImportError:
    HAS_RPI_GPIO = False

from .base_gpio import BaseGpioBackend


class RpiGpioBackend(BaseGpioBackend):
    """
    Raspberry Pi GPIO backend
    """

    def __init__(self, debug = False):
        if not HAS_RPI_GPIO:
            raise ImportError("RPi.GPIO module is not installed")
        self.debug = debug
        gpio.setmode(gpio.BCM)

    def setup_channel(self, channel, mode, pull=None):
        if self.debug:
            print(f"RPiGPIO: Setting channel {channel} to mode {mode} with pull {pull}")
        if pull == self.PULL_UP:
            pud = gpio.PUD_UP
        elif pull == self.PULL_DOWN:
            pud = gpio.PUD_DOWN

        if mode == self.MODE_OUT:
            gpio.setup(channel, gpio.OUT)
        elif mode == self.MODE_IN:
            gpio.setup(channel, gpio.IN, pull_up_down=pud)

    def clean_up(self):
        if self.debug:
            print("RPiGPIO: Cleaning up")
        gpio.cleanup()

    def set_output(self, channel, state):
        if self.debug:
            print(f"RPiGPIO: Setting channel {channel} to state {state}")
        if state == self.STATE_HIGH:
            gpio.output(channel, 1)
        elif state == self.STATE_LOW:
            gpio.output(channel, 0)

    def get_input(self, channel):
        if self.debug:
            print(f"RPiGPIO: Getting channel {channel} (returning LOW)")
        state = gpio.input(channel)
        if state:
            return self.STATE_HIGH
        else:
            return self.STATE_LOW
