from interface import Interface
import logging
import yaml
import time
import sys

# Logging
fname = time.strftime("%Y%m%d-%H%M%S")
fname = ""
flognamestr = "logfile{:s}.txt".format(fname)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    #format="%(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(flognamestr, 'w+'),
    ])


with open("config.yml") as stream: # QUELLE: https://stackoverflow.com/questions/1773805/how-can-i-parse-a-yaml-file-in-python
            try:
                config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logging.error(exc)

Interface(config)