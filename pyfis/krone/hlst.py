"""
Copyright (C) 2019 - 2020 Julian Metzler

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

from .k9000_rs485 import Krone9000RS485Controller


class Krone9000HLST(Krone9000RS485Controller):
    """
    Controls a HLST (Heizungs- und Lichtsteuerung)
    (heater, fan and light control) board.
    """
    
    BOARD_ID = 0x10
    
    CMD_GET_STATUS = 0x01
    CMD_LOCK = 0xC6
    CMD_UNLOCK = 0xC7
    CMD_CONTROL = 0x0A
    
    def build_parameters(self, light, heater, fan, force_heater, force_fan, low_min_temp):
        """
        light: 1=on, 0=off
        heater: 1=on, 0=off
        fan: 1=on, 0=off
        force_heater: 1=force on, 0=automatic
        force_fan: 1=force on, 0=automatic
        low_min_temp: 1=-20°C temperature limit, 0=0°C temperature limit
        """
        parameter_byte = 0x00
        parameter_byte |= int(light) << 7
        parameter_byte |= int(heater) << 6
        parameter_byte |= int(fan) << 5
        parameter_byte |= int(force_heater) << 2
        parameter_byte |= int(force_fan) << 1
        parameter_byte |= int(low_min_temp)
        return parameter_byte
    
    def send_heartbeat(self, address):
        return super().send_heartbeat(self.BOARD_ID, address)
    
    def control(self, address, light, heater, fan, force_heater, force_fan, low_min_temp):
        return self.send_command(self.BOARD_ID, address, self.CMD_CONTROL, self.build_parameters(light, heater, fan, force_heater, force_fan, low_min_temp))
