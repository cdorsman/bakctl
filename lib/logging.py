import logging
from datetime import datetime

date: str = datetime.today().strftime('%Y%m%d%H%M%S')
logging.basicConfig(filename=f'bakctl-{date}.log', level=logging.INFO)
logger = logging.getLogger('bakctl')
