"""
Copyright (C) 2020 - 2023 Julian Metzler

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

import argparse

from pyfis.omega import OmegaRS485Controller


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=str, required=True)
    parser.add_argument("-a", "--address", type=int, required=True)
    args = parser.parse_args()

    c = OmegaRS485Controller(args.port)
    serial = c.read_serial_number(args.address)
    if not serial:
        print("Failed to connect to module!")
        return
    print("Module serial number:", " ".join(["{:02X}".format(byte) for byte in serial]))
    confirm = input("Start calibration? [Y/n]: ").lower() in ("", "y")
    if not confirm:
        print("Aborted")
        return
    c.calibration_start(args.address)

    try:
        while True:
            input("Step calibration: Press Enter until a flap falls, then press Ctrl+C.")
            c.calibration_step(args.address)
    except KeyboardInterrupt:
        pass

    try:
        while True:
            input("Pulse calibration: Press Enter until a flap falls, then press Ctrl+C.")
            c.calibration_pulse(args.address)
    except KeyboardInterrupt:
        pass

    new_position = int(input("Please enter the current flap position: "))
    c.calibration_finish(args.address, new_position)
    print("Done!")


if __name__ == "__main__":
    main()
