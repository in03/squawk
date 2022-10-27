import subprocess
import logging
from typing import Union

import torch
from squawk.utils import core
from rich.prompt import Confirm
from squawk.settings import SettingsManager
from yaspin import yaspin
from rich import print

# import pkg_info

settings = SettingsManager()
logger = logging.getLogger(__name__)
logger.setLevel(settings["app"]["loglevel"])


def check_for_updates(github_url: str, package_name: str) -> Union[dict, None]:

    """Compare git origin to local git or package dist for updates

    Args:
        - github_url(str): origin repo url
        - package_name(str): offical package name

    Returns:
        - dict:
            - 'is_latest': bool,
            - 'current_version': git_short_sha

    Raises:
        - none
    """

    latest = False

    spinner = yaspin(
        text="Checking for updates...",
        color="cyan",
    )
    spinner.start()

    build_info = pkg_info.get_build_info(package_name)
    if build_info["build"] != "git":

        spinner.fail("❌ ")
        logger.warning(
            "[yellow][bold]WIP:[/bold] Currently unable to check for release updates[/]"
        )
        return None

    if not build_info["version"]:

        spinner.fail("❌ ")
        logger.warning("[yellow]Unable to retrieve package version[/]")
        return None

    if not settings["app"]["check_for_updates"]:

        return {
            "is_latest": None,
            "remote_commit": None,
            "package_commit": build_info["version"],
            "commit_short_sha": build_info["version"][:7:],
        }

    remote_commit = pkg_info.get_remote_current_commit(github_url)

    if not remote_commit or not build_info["version"]:

        spinner.fail("❌ ")
        logger.warning("[red]Failed to check for updates[/]")
        return None

    elif remote_commit != build_info["version"]:

        spinner.ok("🔼 ")
        logger.warning(
            "[yellow]Update available.\n"
            + "Fully uninstall and reinstall when possible:[/]\n"
            + '"pip uninstall resolve-squawk"\n'
            + f'"pip install git+{github_url}"\n'
        )

        logger.debug(f"Remote: {remote_commit}")
        logger.debug(f"Current: {build_info['version']}")

    else:

        latest = True
        spinner.ok("✨ ")

    return {
        "is_latest": latest,
        "remote_commit": remote_commit,
        "package_commit": build_info["version"],
        "commit_short_sha": build_info["version"][:7:],
    }


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
