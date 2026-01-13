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

from .base_serial import BaseSerialPort
from .serial import SerialPort

try:
    import serial
    has_serial = True
except ImportError:
    has_serial = False


def is_serial_port(port):
    if has_serial:
        return isinstance(port, serial.Serial) or isinstance(port, BaseSerialPort)
    else:
        return isinstance(port, BaseSerialPort)

def ensure_serial_port(port, *args, **kwargs):
    if is_serial_port(port):
        return port
    else:
        return SerialPort(port, *args, **kwargs)