import sys

from pyfis.krone import *
from pyfis.krone.util import *

fbm = KroneFBMController("/dev/ttyUSB5")
fbm.set_code(0, ord(sys.argv[1].upper()))
fbm.set_all()