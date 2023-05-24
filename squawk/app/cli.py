#!/usr/bin/env python3.6

from enum import Enum
import logging
import os
from typing import Optional

import typer
from pyfiglet import Figlet
from rich import print, traceback
from rich.console import Console
from rich.rule import Rule
from rich.prompt import Confirm
from pydavinci import davinci
from pydavinci.exceptions import ObjectNotFound
from squawk.app import main
from squawk.utils import core, pkg_info

# TODO: Add global option to hide banner
# labels: enhancement
hide_banner = typer.Option(
    default=False, help="Hide the title and build info on startup"
)

from squawk.settings import dotenv_settings_file, user_settings_file
from squawk.settings.manager import settings

logger = logging.getLogger("squawk")
logger.setLevel(settings.app.loglevel)
traceback.install(show_locals=False)

# Init classes
cli_app = typer.Typer()
config_app = typer.Typer()
cli_app.add_typer(config_app, name="config")

console = Console()
resolve = davinci.Resolve()


# Special functions


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


@cli_app.callback(invoke_without_command=True)
def global_options(
    ctx: typer.Context,
):
    draw_banner()
    print(
        "\nConfigurable, AI-powered transcriptions for DaVinci Resolve\n"
        "https://github.com/in03/squawk\n"
    )


# Commands


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

    media_file = main.render_timeline(settings.app.working_dir)
    srt_file = main.tts(media_file)
    main.import_srt(srt_file)


@cli_app.command("file")
def transcribe_file(media_file: str):
    """
    Transcribe a media file and import the transcription into Resolve.

    Args:
        media_file (str): Path to an ffmpeg supported media file.
    """

    if not os.path.exists(media_file):
        print(f"[red]Sorry, no file found at path: '{media_file}'")
        core.app_exit(1, -1)

    srt_file = main.tts(media_file)
    main.import_srt(srt_file)


@config_app.callback(invoke_without_command=True)
def config_callback(ctx: typer.Context):
    """
    Manage Squawk's configuration

    Squawk's configuration is layered.

    Toml is populated with modifiable defaults.

    .env overrides toml configuration.
    Environment variables override .env and toml.

    Run `--help` on any of the below commands for further details.
    """

    # Ensure 'user_settings_file' exists
    if not os.path.exists(user_settings_file):
        with open(user_settings_file, "x"):
            print("[cyan]Initialised user toml config file")

    # Ensure 'dotenv_settings_file' exists
    if not os.path.exists(dotenv_settings_file):
        with open(dotenv_settings_file, "x"):
            print("[cyan]Initialised dotenv config file")

    if ctx.invoked_subcommand:
        return
    from squawk.settings.manager import settings

    if settings:
        print("[[magenta]Consolidated configuration]")
        print(settings.dict())
        from squawk.settings.regrouping_rules import parsed_rules
        print(parsed_rules)


class RWConfigTypes(str, Enum):
    """Read and writable config types"""

    dotenv = "dotenv"
    toml = "toml"


class RConfigTypes(str, Enum):
    """Readable config types"""

    env = "env"
    dotenv = "dotenv"
    toml = "toml"


@config_app.command("view")
def view_configuration(
    config_type: RConfigTypes = typer.Argument(
        ..., help="View configuration", show_default=False
    )
):
    """
    Print the current user configuration to screen.

    Supply a configuration type to view, or run
    `proxima config` to see consolidated configuration.
    """

    match config_type:
        case "dotenv":
            print("[[magenta]Proxima dotenv configuration]")
            print(
                Syntax.from_path(
                    dotenv_settings_file, theme="nord-darker", line_numbers=True
                )
            )

        case "env":
            print("[[magenta]Proxima environment variables]")

            prefix: str = "PROXIMA"
            variables: dict[str, str] = {}
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    variables.update({key: value})

            [print(f"{x}={os.environ[x]}") for x in variables]
            return

        case "toml":
            print("[[magenta]Proxima toml configuration]")
            print(
                Syntax.from_path(
                    user_settings_file, theme="nord-darker", line_numbers=True
                )
            )

        case _:
            raise typer.BadParameter(f"Unsupported config type: '{config_type}'")


@config_app.command("edit")
def edit_configuration(
    config_type: RWConfigTypes = typer.Argument(
        ..., help="Edit configuration", show_default=False
    )
):
    """
    Edit provided user configuration.

    Note that environment variables, while supported,
    are not editable here.

    Modify them in your own shell environment.
    """

    match config_type:
        case "dotenv":
            print("[cyan]Editing .env config file")
            typer.launch(str(dotenv_settings_file))
            return

        case "toml":
            print("[cyan]Editing user toml config file")
            typer.launch(str(user_settings_file))

        case _:
            raise typer.BadParameter(f"Unsupported config type: '{config_type}'")


@config_app.command("reset")
def reset_configuration(
    config_type: RWConfigTypes = typer.Argument(
        ..., help="Reset configuration", show_default=False
    ),
    force: bool = typer.Option(
        False, "--force", help="Bypass any confirmation prompts.", show_default=False
    ),
):
    """
    Reset the provided user configuration type.

    Be aware that this is IRREVERSIBLE.
    """

    if not force:
        if not Confirm.ask(
            "[yellow]Woah! The action you're about to perform is un-undoable![/]\n"
            f"Are you sure you want to reset the {config_type} configuration file to defaults?"
        ):
            return

    match config_type:
        case "dotenv":
            with open(dotenv_settings_file, "w"):
                print("[cyan]Reset toml config file to defaults")
                return

        case "toml":
            os.remove(user_settings_file)
            print("[cyan]Reset toml config to defaults")
            return


@config_app.command("reset")
def reset_all_configuration(
    force: bool = typer.Option(
        False, "--force", help="Bypass any confirmation prompts.", show_default=False
    )
):
    """
    Reset ALL user configuration types to defaults.

    This will result in '.env' being made empty
    and 'user_settings.toml' being reset to default values.

    Environment variables will NOT be unset.
    Run `proxima view env` to see their current values.
    """

    # Prompt for confirmation if not forced
    if not force:
        if not Confirm.ask(
            "[yellow]Woah! The action you're about to perform is un-undoable![/]\n"
            "Are you sure you want to reset all user configuration to defaults?"
        ):
            return

    reset_configuration(config_type=RWConfigTypes.dotenv, force=True)
    reset_configuration(config_type=RWConfigTypes.toml, force=True)



# RUN
cli_app()
