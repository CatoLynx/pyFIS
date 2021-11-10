"""
Copyright (C) 2021 Julian Metzler

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


def debug_hex(message, readable_ascii = False, readable_ctrl = False):
    """
    Turn a message into a readable form
    """

    CTRL_CHARS = {
        0x02: "STX",
        0x03: "ETX",
        0x04: "EOT",
        0x05: "ENQ",
        0x10: "DLE",
        0x15: "NAK",
        0x17: "ETB"
    }

    result = []
    for byte in message:
        if readable_ctrl and byte in CTRL_CHARS:
            result.append(CTRL_CHARS[byte])
        elif readable_ascii and byte not in range(0, 32) and byte != 127:
            result.append(chr(byte))
        else:
            result.append("{:02X}".format(byte))
    return " ".join(result)