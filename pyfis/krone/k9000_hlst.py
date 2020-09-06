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
    BOARD_NAME = "HLST"
    
    CMD_GET_STATUS = 0x01
    CMD_LOCK = 0xC6
    CMD_UNLOCK = 0xC7
    CMD_CONTROL = 0x0A
    
    def _build_parameters(self, light, heater, fan, force_heater, force_fan, low_min_temp):
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
    
    def get_status(self):
        # Get the status of the FBK board
        payload = self.send_command(self.CMD_GET_STATUS, response=True)
        stat1 = payload[1]
        stat2 = payload[2]
        status = {
            'comm_err': bool(stat1 & 0x40),
            'reset': bool(stat1 & 0x20),
            'locked': bool(stat1 & 0x10),
            'light_err': bool(stat1 & 0x08),
            'hlst_err': bool(stat1 & 0x04),
            'force_ctrl': bool(stat1 & 0x02),
            'low_min_temp': bool(stat1 & 0x01),
            'light_on_set': bool(stat2 & 0x80),
            'heater_on': bool(stat2 & 0x40),
            'fan_on': bool(stat2 & 0x20),
            'light_on_feedback': bool(stat2 & 0x10),
            'temp_above_40c': bool(stat2 & 0x08),
            'temp_above_0c': bool(stat2 & 0x04),
            'temp_above_neg20c': bool(stat2 & 0x02),
            'sw_ver': f"{payload[3]}.{payload[4]}"
        }
        return status
    
    def lock(self):
        # Lock the entire HLST
        return self.send_command(self.CMD_LOCK)
    
    def unlock(self):
        # Unlock the entire HLST
        return self.send_command(self.CMD_UNLOCK)
    
    def control(self, light, heater, fan, force_heater, force_fan, low_min_temp):
        return self.send_command(self.CMD_CONTROL, self._build_parameters(light, heater, fan, force_heater, force_fan, low_min_temp))
