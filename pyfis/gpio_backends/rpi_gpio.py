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

import RPi.GPIO as gpio


class RpiGpioBackend:
    """
    Raspberry Pi GPIO backend
    """

    MODE_IN = 1
    MODE_OUT = 2

    PULL_UP = 1
    PULL_DOWN = 2

    STATE_HIGH = 1
    STATE_LOW = 0

    def __init__(self, debug = False):
        self.debug = debug
        gpio.setmode(gpio.BCM)

    def setup_channel(self, channel, mode, pull=None):
        if pull == self.PULL_UP:
            pud = gpio.PUD_UP
        elif pull == self.PULL_DOWN:
            pud = gpio.PUD_DOWN

        if mode == self.MODE_OUT:
            gpio.setup(channel, gpio.OUT)
        elif mode == self.MODE_IN:
            gpio.setup(channel, gpio.IN, pull_up_down=pud)

    def clean_up(self):
        gpio.cleanup()

    def set_output(self, channel, state):
        if state == self.STATE_HIGH:
            gpio.output(channel, 1)
        elif state == self.STATE_LOW:
            gpio.output(channel, 0)

    def get_input(self, channel):
        state = gpio.input(channel)
        if state:
            return self.STATE_HIGH
        else:
            return self.STATE_LOW
