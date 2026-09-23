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


class BaseGpioBackend:
    """
    GPIO backend base class
    """

    MODE_IN = 1
    MODE_OUT = 2

    PULL_UP = 1
    PULL_DOWN = 2

    STATE_HIGH = 1
    STATE_LOW = 0

    def __init__(self, debug = False):
        pass

    def setup_channel(self, channel, mode, pull=None):
        raise NotImplementedError

    def clean_up(self):
        raise NotImplementedError

    def set_output(self, channel, state):
        raise NotImplementedError

    def get_input(self, channel):
        raise NotImplementedError
