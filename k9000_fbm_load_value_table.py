import argparse
import sys

from pyfis.krone import Krone9000FBM


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
    parser.add_argument("-a", "--addr", type=int, required=True)
    parser.add_argument("-t", "--table", type=str, required=False)
    args = parser.parse_args()
    
    fbm = Krone9000FBM(args.port, exclusive=True)
    
    if args.table:
        table = read_value_table(args.table)
    else:
        table = None
    
    while True:
        action = input("What to do? [Code/Status/Letter/Home/WrtTbl/DelTbl/Exit] ").upper()
        if action.startswith("C"):
            sys.stdout.write("  FBM Code: ")
            code = fbm.read_code(args.addr)
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
        elif action.startswith("S"):
            sys.stdout.write("  FBM Status: ")
            try:
                print(fbm.get_status(args.addr))
            except:
                print("No data received!")
                continue
        elif action.startswith("L"):
            if len(action) < 2:
                print("  No letter specified!")
                continue
            letter = action[1]
            fbm.set_code(args.addr, ord(letter[0]))
            fbm.set_all()
        elif action.startswith("H"):
            print("  Rotating to home position")
            fbm.set_home()
        elif action.startswith("W"):
            if not table:
                print("  No value table loaded!")
                continue
            print("  Writing value table")
            for pos, value in table.items():
                print(f"    Writing flap {pos}: {chr(value)}")
                resp = fbm.set_table(args.addr, value, pos)[0]
        elif action.startswith("D"):
            if not table:
                print("  No value table loaded!")
                continue
            print("  Deleting value table")
            resp = fbm.delete_table(args.addr)[0]
        elif action.startswith("E"):
            break
        


if __name__ == "__main__":
    main()