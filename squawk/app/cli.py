#!/usr/bin/env python3.6

import logging
from typing import Optional

import typer
from pyfiglet import Figlet
from rich import print, traceback
from rich.console import Console
from rich.rule import Rule
from pydavinci import davinci
from pydavinci.exceptions import ObjectNotFound
from squawk.app import main
from squawk.utils import core, pkg_info

# TODO: Add global option to hide banner
# labels: enhancement
hide_banner = typer.Option(
    default=False, help="Hide the title and build info on startup"
)

from squawk.settings import SettingsManager

settings = SettingsManager()
logger = logging.getLogger(__name__)
logger.setLevel(settings["app"]["loglevel"])
traceback.install(show_locals=False)

# Init classes
cli_app = typer.Typer()

console = Console()
resolve = davinci.Resolve()


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
def config():
    """Open user settings configuration file for editing"""

    from squawk.settings import SettingsManager

    settings = SettingsManager()

    print("\n")
    console.rule(
        f"[green bold]Open 'user_settings.yaml' config[/] :gear:", align="left"
    )
    print("\n")

    typer.launch(settings.user_file)


@cli_app.command("timeline")
def transcribe_timeline(timeline_name: Optional[str] = typer.Argument(None)):

    """
    Transcribe a Resolve timeline and import the transcription into Resolve.
    """

    if resolve.project.is_rendering():
        logger.error(
            "[red]Resolve is currently rendering. We can't add any more jobs until it's finished"
        )

    # Change to edit page to clear any glitchy read-only mode
    resolve.page = "edit"

    # Switch if timeline chosen
    if timeline_name:

        try:
            resolve.project.open_timeline(timeline_name)
        except ObjectNotFound:
            logger.error(
                f"[red]Could not open timeline[/] '{timeline_name}'"
                "Are you sure it exists?"
            )
            core.app_exit(1, -1)
    else:
        timeline_name = resolve.active_timeline.name

    print("\n")
    console.rule(
        f"[green bold]Transcribing audio on timeline {timeline_name}[/] :outbox_tray:",
        align="left",
    )
    print("\n")

    media_file = main.render_timeline(settings["paths"]["working_dir"])
    srt_file = main.tts(media_file)
    main.import_srt(srt_file)


@cli_app.command("file")
def transcribe_file(media_file: str):
    """
    Transcribe a media file and import the transcription into Resolve.

    Args:
        media_file (str): Path to an ffmpeg supported media file.
    """
    srt_file = main.tts(media_file)
    main.import_srt(srt_file)


# RUN
cli_app()
