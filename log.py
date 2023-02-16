import logging
import sys

# init logging
logger = logging.getLogger()
fh = logging.FileHandler('refreshMetadata.log', encoding='utf-8', mode='w')
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - refreshMetadata.py - %(message)s")
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)
logger.setLevel(logging.INFO)
