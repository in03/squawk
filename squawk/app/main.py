import logging
import os
import sys
import time
from datetime import datetime
from time import sleep

import whisper
from pydavinci import davinci
from rich import traceback
from rich.console import Console
from rich.progress import Progress
from squawk.settings import SettingsManager
from squawk.utils import core
from whisper import utils as whisper_utils

# Init
settings = SettingsManager()
logger = logging.getLogger(__name__)
logger.setLevel(settings["app"]["loglevel"])
traceback.install(show_locals=False)

resolve = davinci.Resolve()
console = Console()


def ensure_path(folder_path: str):
    """
    Create a nested folder structure from path in Resolve's media pool.

    Since it's using a path, it can only create one subfolder at a time.
    Not a whole tree. Use it to create/ensure an output path.
    It also maintains last folder selection, so you don't need to reselect it.

    Args:
        folder_path (str): Path to create folder structure from
    """

    # cross platformish
    folder_path = folder_path.replace("\\", "/")
    path_segments = folder_path.split("/")
    path_segments = [x for x in path_segments if x != ""]

    resolve = davinci.Resolve()
    media_pool = resolve.media_pool
    root_folder = media_pool.root_folder

    def get_subfolder(parent_folder, subfolder_name: str):
        """
        Return a subfolder by name within a given parent folder.

        Args:
            current_folder (Folder): _description_
            subfolder_name (str): _description_

        Returns:
            Folder: Subfolder as media pool folder object
        """
        for x in parent_folder.subfolders:
            if x.name == subfolder_name:
                return x
        return None

    # Started from the bottom now we're here
    media_pool.set_current_folder(root_folder)
    current_folder = root_folder

    for i, seg in enumerate(path_segments):

        # If folder exists, navigate
        current_folder = media_pool.current_folder
        if sub := get_subfolder(current_folder, seg):
            logger.debug(f"[magenta]Found subfolder '{sub.name}'")
            media_pool.set_current_folder(sub)
            continue

        # If not, make the whole structure
        remaining_segs = path_segments[i:]

        for x in remaining_segs:

            current_folder = media_pool.current_folder
            logger.debug(
                f"[magenta]Creating subfolder '{x}' in '{current_folder.name}'"
            )
            new_folder = media_pool.add_subfolder(x, current_folder)
            if not media_pool.set_current_folder(new_folder):

                logger.error(
                    f"Couldn't create subfolder '{x}'"
                    f"for path '{folder_path}' in media pool"
                )
        logger.debug("[magenta]Created folder structure")
        return

    logger.debug("[magenta]Found all folders. Nothing created")
    return


def render_timeline(output_path: str) -> str:

    project = resolve.project
    timeline = resolve.active_timeline

    custom_name = (
        f"{project.name} - {timeline.name} - {datetime.now().strftime('%H%M%S')}"
    )
    output_file = os.path.join(output_path, custom_name + ".mov")

    # Open deliver page
    resolve.page = "deliver"

    # Standard included preset - palette cleanser for weird file suffixes
    assert project.load_render_preset("H.264 Master")

    render_settings = {
        "SelectAllFrames": True,
        "ExportVideo": False,
        "ExportAudio": True,
        "FormatWidth": 1280,  # Necessary
        "FormatHeight": 720,  # Necessary
        "AudioCodec": "aac",  # Not working?
        "AudioBitDepth": 16,
        "AudioSampleRate": 48000,
        "CustomName": custom_name,
        "TargetDir": output_path,
    }

    assert project.set_render_settings(render_settings)
    render_job_id = project.add_renderjob()
    assert render_job_id

    logger.info(f"[yellow]Rendering '{output_file}'")
    core.notify("Squawk", f"Rendering '{output_file}'")

    try:

        if not project.render([render_job_id], interactive=False):
            logger.error(
                f"[red]Couldn't render job: [/]'{render_job_id}'"
                "Please make sure the timeline isn't read-only if you're in collaborative mode."
            )
            core.app_exit(1, -1)

        with Progress(transient=True) as progress:

            job_status = "Pending..."
            progress_bar = progress.add_task(job_status, completed=0, total=100)

            while True:

                if job_status == "Complete":
                    logger.info("[green]Render completed!")
                    break

                elif job_status == "Cancelled":
                    logger.error("[red]User cancelled job in Resolve")
                    core.app_exit(1, -1)

                status = project.render_status(render_job_id)
                logger.debug(status)

                job_status = str(status["JobStatus"])
                percentage = float(status.get("CompletionPercentage", 0.0))

                progress.update(
                    progress_bar, completed=percentage, description=job_status
                )
                sleep(0.2)

        logger.debug(f"[magenta]Media file: {output_file}")
        core.notify("Squawk", "Finished rendering")

        return output_file

    except KeyboardInterrupt:

        # assert resolve.project.delete_renderjob(render_job_id) # Can we stop just a single job?
        logger.error("[red]User aborted - cancel render manually!")
        # core.notify("Squawk", "Aborted render!")
        core.app_exit(1, -1)


def tts(media_file: str) -> str:

    if not os.path.exists(media_file):
        raise FileNotFoundError(f"Media file: {media_file} not found!")

    model = whisper.load_model(settings["text_to_speech"]["model"])

    core.notify("Squawk", "Starting transcription")
    start_time = time.time()

    with Progress(transient=True) as progress:

        progress.add_task("[yellow]Transcribing", total=None)

        if settings["text_to_speech"]["translate_to_english"]:
            result = model.transcribe(media_file, task="translate")
        else:
            result = model.transcribe(media_file)

    core.notify(
        "Squawk", f"Processing finished after {int(time.time() - start_time)} seconds"
    )

    srt_path = os.path.join(
        settings["paths"]["working_dir"], (os.path.basename(media_file) + ".srt")
    )
    with open(srt_path, "w", encoding="utf-8") as srt:
        whisper_utils.write_srt(result["segments"], file=srt)

    return srt_path


def import_srt(srt_file):
    """
    Import SRT file into Resolve
    """

    resolve.page = "edit"
    media_pool = resolve.media_pool

    # Create or find path for srt file
    ensure_path(settings["resolve"]["subtitle_folder_path"])

    logger.info(f"[cyan]Importing SRT file: '{srt_file}'")
    mpi = media_pool.import_media([srt_file])
    assert mpi
    logger.debug(f"[magenta]Media pool item: {[mpi]}")
