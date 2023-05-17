import logging

from squawk.settings.manager import settings
from rich import print

# import pkg_info

logger = logging.getLogger("squawk")
logger.setLevel(settings.app.loglevel)