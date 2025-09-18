import argparse
import sys
import time

from pyfis.krone import Krone9000FBM
from pyfis.krone.util import calibrate_fbm_interactive


def read_value_table(filename):
    """
    Read the value table in KRONE .DAT format
    and return it as a dict
    """
    
    with open(filename, 'r', encoding='latin-1') as f:
        lines = [line.strip() for line in f.readlines()]
    
    table = {}
    for line in lines:
        if not line:
            continue
        try:
            parts = line.split(";")
            remainder = ";".join(parts[1:])
            pos = int(parts[0])
            if remainder.startswith("0x"):
                value = int(remainder.split(";")[0], 16)
            else:
                value = ord(remainder[0])
            table[pos] = value
        except:
            continue
    return table


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=str, required=True)
    parser.add_argument("-t", "--table", type=str, required=False)
    parser.add_argument("-d", "--debug", action='store_true')
    args = parser.parse_args()
    
    fbm = Krone9000FBM(args.port, exclusive=True, debug=args.debug)
    
    if args.table:
        table = read_value_table(args.table)
    else:
        table = None
    
    while True:
        data = input("What to do? [Code/Status/Letter/Text/Home/Wrttbl/Deltbl/caliBrate/Autotest/Exit] ").upper()
        fbm.port.read(fbm.port.inWaiting()) # Flush buffer
        if not data:
            continue
        action = data[0]
        if action not in ("H", "E"):
            if len(data) < 2:
                print("  No address specified!")
                continue
            if action == "L":
                addr = int(data[1:-1])
            else:
                addr = int(data[1:])
        if action == "C":
            code = fbm.read_code(addr)
            sys.stdout.write("  FBM Code: ")
            if len(code) < 1:
                print("No data received!")
                continue
            code = code[0]
            if code == 0x10:
                print("Undefined position")
            elif code == 0x20:
                print("Home position")
            elif code < 0x20:
                print(f"Unknown status code 0x{code:02X}")
            else:
                print(chr(code))
        elif action == "S":
            try:
                fbm_status = fbm.get_status(addr) or ["OK"]
                print("  FBM Status:", ", ".join(fbm_status))
            except:
                print("  FBM Status: No data received!")
                continue
        elif action == "L":
            if len(data) < 3:
                print("  No letter specified!")
                continue
            letter = data[-1]
            fbm.set_code(addr, ord(letter[0]))
            fbm.set_all()
        elif action == "T":
            text = input("  Enter text: ").upper()
            fbm.set_text(text, addr)
            fbm.set_all()
        elif action == "H":
            print("  Rotating to home position")
            fbm.set_home()
        elif action == "W":
            if not table:
                print("  No value table loaded!")
                continue
            print("  Writing value table")
            for pos, value in table.items():
                print(f"    Writing flap {pos}: {chr(value)}")
                resp = fbm.set_table(addr, value, pos)[0]
        elif action == "D":
            if not table:
                print("  No value table loaded!")
                continue
            print("  Deleting value table")
            resp = fbm.delete_table(addr)[0]
        elif action == "B":
            if addr != 0:
                print("  Calibration is only possible for address 0!")
                continue
            calibrate_fbm_interactive(fbm, addr)
        elif action == "A":
            print("  Performing test routine")

            def _expect_code(code):
                for i in range(20):
                    time.sleep(0.5)
                    status = ", ".join(fbm.get_status(addr) or ["OK"])
                    print(f"      Status: {status}")
                    if status == "OK":
                        break
                    elif i == 19:
                        print("      Error: Incorrect status!")
                        return False
                actual_code = fbm.read_code(addr)
                if len(actual_code) < 1:
                    print("      No data received!")
                    return False
                actual_code = actual_code[0]
                if actual_code != code:
                    print(f"      Error: FBM reports code 0x{actual_code:02X} ({actual_code}, letter {chr(actual_code)}) instead of 0x{code:02X} ({code}, letter {chr(code)})")
                    return False
                return True

            result = False
            for letter in ("0", "A", "M", "Z", "="):
                print(f"    Rotating to letter {letter}")
                fbm.set_code(addr, ord(letter))
                fbm.set_all()
                result = _expect_code(ord(letter))
                if not result:
                    break
                else:
                    print(f"      Success")
                time.sleep(1)
            if not result:
                continue

            print("    Rotating to home position")
            fbm.set_home()
            result = _expect_code(0x20)
            if not result:
                continue
            else:
                print(f"      Success")
        elif action == "E":
            break
        


if __name__ == "__main__":
    main()
