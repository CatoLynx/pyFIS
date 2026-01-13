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


def high16(value):
    # Get high byte of a 16-bit value
    return value >> 8

def low16(value):
    # Get low byte of a 16-bit value
    return value & 0xFF

def int_to_bcd(value):
    # Turn a positive integer into its hexadecimal BCD representation.
    # E.g. 37 => 0x37
    result = 0x00
    value_str = str(value)
    for pos, char in enumerate(value_str[::-1]):
        result += int(char) * 16**pos
    return result