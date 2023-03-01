import subprocess
import logging

import torch
from squawk.settings import SettingsManager
from rich import print

# import pkg_info

settings = SettingsManager()
logger = logging.getLogger(__name__)
logger.setLevel(settings["app"]["loglevel"])


def check_for_cuda():
    """
    Check for presence of supported Nvidia card

    Will only return true if present and correct drivers are installed.

    Returns:
        bool: return `True` if present, `False` if not
    """

    def check_command_output(command: str | list[str]) -> bool:
        try:
            subprocess.check_output(command)
        except Exception:
            return False
        else:
            return True

    if not check_command_output("nvidia-smi"):
        logger.debug(
            "[red]Nvidia card or drivers are not installed, falling back to CPU..."
        )
        return False
    else:
        logger.debug("[green]Supported CUDA device detected")

    if not check_command_output(["nvcc", "--version"]):
        logger.error(
            "[red]Nvidia card detected, but CUDA not available, falling back to CPU..."
        )
        return False
    else:
        logger.debug("[green]Supported CUDA drivers installed")

    if not torch.cuda.is_available():
        logger.error("[red]Torch CUDA version isn't installed, falling back to CPU...")
        return False

    print(f"[magenta]CUDA supported: [/]'{torch.cuda.get_device_name(0)}' :fire:")
    return True
