"""
Copyright (C) 2020 Julian Metzler

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


import time


def calibrate_fbm_interactive(fbm, addr):
    """
    Interactive process for calibrating the flap count
    and home position on small FBM units
    """
    print("\nStep 0: Testing home position")
    print("Check if calibration is necessary by moving to the home position")
    print("and seeing if the unit hits it correctly.")
    input("Press Enter to start.")
    fbm.set_home()
    print("\nWait for the unit to stop rotating!")
    time.sleep(3)
    res = ""
    while res not in ("Y", "N"):
        res = input("Was the home position reached? [Y/N]: ").upper()
        if res == "Y":
            print("\nGreat! No need to calibrate.")
            return
    
    print("Step 1: Flap count (BR1) calibration")
    print("The unit will rotate once or twice and stop.")
    print("There is no need to do anything while it is rotating.")
    input("Press Enter to start.")
    fbm.start_calibration_br1()
    print("\nWait for the unit to stop rotating!")
    time.sleep(5)
    
    success = False
    back_to_step_2 = False
    while not success:
        exit_step_2 = False
        while not exit_step_2:
            print("\nStep 2: Home position (BR2) calibration")
            print("The unit will start rotating.")
            print("As soon as the desired home position is reached, hit Enter.")
            print("This might take a few tries.")
            print("The unit should complete one more rotation after you hit Enter!")
            print("If the unit stops rotating as soon as you hit Enter,")
            print("your timing was not correct. Try again in this case.")
            input("Press Enter to start and get ready to hit Enter again!")
            fbm.start_calibration_br2()
            input("Press Enter if the home position is reached!")
            fbm.stop_calibration()
            print("\nWait for the unit to stop rotating!")
            res = ""
            while res not in ("Y", "N"):
                res = input("Was the desired position reached? [Y/N]: ").upper()
                if res == "Y":
                    exit_step_2 = True
        
        print("\nStep 3: Testing home position")
        print("Test the calibration by moving to the home position again")
        print("and seeing if the unit hits it correctly.")
        input("Press Enter to start.")
        fbm.set_home()
        print("\nWait for the unit to stop rotating!")
        time.sleep(3)
        res = ""
        while res not in ("Y", "N"):
            res = input("Was the home position reached? [Y/N]: ").upper()
            if res == "N":
                success = False
                back_to_step_2 = True
                break
            elif res == "Y":
                back_to_step_2 = False
                break
        
        if back_to_step_2:
            continue
        
        exit_step_4 = False
        while not exit_step_4:
            print("\nStep 4: Testing characters")
            print("Test the calibration by entering letters")
            print("and seeing if the unit hits them correctly.")
            char = ""
            while len(char) != 1 or ord(char) not in range(128):
                char = input("Enter a character to test or nothing to finish: ").upper()
                if char == "":
                    exit_step_4 = True
                    success = True
                    break
                if len(char) > 1 or ord(char) not in range(128):
                    continue
                else:
                    fbm.set_code(addr, ord(char))
                    time.sleep(0.1)
                    fbm.set_all()
                    time.sleep(0.1)
                    res = ""
                    while res not in ("Y", "N"):
                        res = input("Was the desired character hit? [Y/N]: ").upper()
                        if res == "N":
                            exit_step_4 = True
                            success = False
    
    fbm.set_home()
    print("\nGreat! The unit is now calibrated.")
