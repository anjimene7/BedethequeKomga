import logging
import sys
from os import getenv

# init logging
logger = logging.getLogger('refreshMetadata')
fh = logging.FileHandler('refreshMetadata.log', encoding='utf-8', mode='w')
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s")
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)
logger.setLevel(getenv('KOMGA_LOG_LEVEL', 'INFO'))
