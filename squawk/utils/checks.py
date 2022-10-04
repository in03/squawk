import logging
from typing import Union

from rich.prompt import Confirm
from squawk.settings import SettingsManager
from yaspin import yaspin

import pkg_info

settings = SettingsManager()

logger = logging.getLogger(__name__)


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
