#!/usr/bin/env python3.6

import logging
import webbrowser
from typing import List, Optional

import typer
from pyfiglet import Figlet
from rich import print, traceback
from rich.console import Console
from rich.rule import Rule
from squawk.utils import core, pkg_info
from squawk.app.transcribe import Transcribe

# TODO: Add global option to hide banner
# labels: enhancement
hide_banner = typer.Option(
    default=False, help="Hide the title and build info on startup"
)

traceback.install()
logger = logging.getLogger(__name__)


# Init classes
cli_app = typer.Typer()
console = Console()


@cli_app.callback(invoke_without_command=True)
def run_without_args():
    draw_banner()
    print("Run [bold]squawk --help[/] for a list of commands")


def draw_banner():

    # Print CLI title
    fig = Figlet(font="rectangles")
    text = fig.renderText("SQUAWK")
    print(text + "\n")

    # Get build info
    build_info = pkg_info.get_build_info("squawk")

    # Print banner data
    if build_info["build"] == "release":

        print(
            f"[bold]{str(build_info['build']).capitalize()} build[/] "
            f"{build_info['version']} | "
        )

    else:

        print(
            f"[bold]{str(build_info['build']).capitalize()} build[/] "
            f"{'([green]installed[/] :package:)' if build_info['installed'] else '([yellow]cloned[/] :hammer_and_wrench:)'} "
            f"'{build_info['version'][:7:]}'"
        )

    Rule()


def run_checks():
    """Run before CLI App load."""

    from squawk.settings import SettingsManager
    from squawk.utils import checks

    settings = SettingsManager()

    # Check for any updates and inject version info into user settings.
    version_info = checks.check_for_updates(
        github_url=settings["app"]["update_check_url"],
        package_name="squawk",
    )

    settings.update({"version_info": version_info})


def cli_init():

    draw_banner()
    run_checks()


# Commands


@cli_app.command()
def tts():
    """
    Queue proxies from the currently open
    DaVinci Resolve timeline
    """

    # Init
    from squawk.settings import SettingsManager

    settings = SettingsManager()
    logger = logging.getLogger(__name__)
    logger.setLevel(settings["app"]["loglevel"])
    # End init

    print("\n")
    console.rule(
        f"[green bold]Queuing proxies from Resolve's active timeline[/] :outbox_tray:",
        align="left",
    )
    print("\n")

    transcribe = Transcribe()
    transcribe.run()


# @cli_app.command(
#     context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
# )
# def celery(
#     ctx: typer.Context,
#     celery_command: List[str] = typer.Argument(..., help="A command to pass to Celery"),
# ):
#     """
#     Pass commands to Celery buried in venv.

#     Runs `celery -A squawk.worker [celery_command]`
#     at the absolute location of the package's Celery executable.
#     Useful when the celery project is buried in a virtual environment and you want
#     to do something a little more custom like purge jobs from a custom queue name.

#     See https://docs.celeryq.dev/en/latest/reference/cli.html for proper usage.
#     """

#     # print(ctx.params["celery_command"])

#     print("\n")
#     console.rule(f"[cyan bold]Celery command :memo:", align="left")
#     print("\n")

#     subprocess.run(
#         [
#             pkg_info.get_script_from_package("celery"),
#             "-A",
#             "squawk.worker",
#             *celery_command,
#         ]
#     )


@cli_app.command()
def config():
    """Open user settings configuration file for editing"""

    from squawk.settings import SettingsManager

    settings = SettingsManager()

    print("\n")
    console.rule(
        f"[green bold]Open 'user_settings.yaml' config[/] :gear:", align="left"
    )
    print("\n")

    # TODO: Cross platform alternative to this hack?
    # labels: enhancement
    webbrowser.open_new(settings.user_file)


def main():
    cli_app()


if __name__ == "__main__":
    main()
