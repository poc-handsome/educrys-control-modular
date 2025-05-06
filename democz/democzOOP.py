import logging
import time
import sys



# Logging
fname = time.strftime("%Y%m%d-%H%M%S")
fname = ""
flognamestr = "./logfile{:s}.txt".format(fname)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    #format="%(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(flognamestr, 'w+'),
    ]
)



# Start DemoCZ
import control
control.Control()
