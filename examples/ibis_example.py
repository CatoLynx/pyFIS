from pyfis.ibis import SerialIBISMaster, TCPIBISMaster


def main():
    # Initialize a serial IBIS Master on serial port /dev/ttyS0 and turn on debug output
    master = SerialIBISMaster("/dev/ttyS0", debug=True)
    
    # For Windows users, use a port like COM1:
    # master = SerialIBISMaster("COM1", debug=True)
    
    # Alternatively, uncomment to use a TCP connection on 192.168.0.42, port 5001:
    # master = TCPIBISMaster("192.168.0.42", 5001, debug=True)
    
    # Send a DS001 telegram (line number 123)
    master.DS001(123)
    
    # Send a DS009 telegram (next stop display text)
    master.DS009("Akazienallee")
    
    # Send a DS003a telegram (destination text)
    master.DS003a("Hauptbahnhof")
    
    # Query status of IBIS device with address 1
    status = master.DS020(1)
    
    # The variable status will contain a dict like this:
    # {'status': 'ok'}


if __name__ == "__main__":
    main()
