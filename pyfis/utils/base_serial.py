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


class BaseSerialPort:
    def __init__(self):
        pass

    def write(self, data):
        raise NotImplementedError

    def read(self, length):
        raise NotImplementedError

    def setRTS(self, state):
        raise NotImplementedError

    def setDTR(self, state):
        raise NotImplementedError

    def getCTS(self):
        raise NotImplementedError

    def getDSR(self):
        raise NotImplementedError

    def getRI(self):
        raise NotImplementedError

    def getCD(self):
        raise NotImplementedError
