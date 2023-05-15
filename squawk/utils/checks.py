import subprocess
import logging

import torch
from squawk.settings import SettingsManager
from rich import print

# import pkg_info

settings = SettingsManager()
logger = logging.getLogger(__name__)
logger.setLevel(settings["app"]["loglevel"])