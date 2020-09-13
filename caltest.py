from pyfis.krone import *
from pyfis.krone.util import *

fbm = KroneFBMController("/dev/ttyUSB5")
calibrate_fbm_interactive(fbm, 0)