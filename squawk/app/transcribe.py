import logging
import os
import time

from squawk.app.resolve import ResolveObjects
from squawk.settings.manager import SettingsManager
from squawk.utils import core

import whisper
from whisper import utils as whisper_utils

logger = logging.getLogger(__name__)

settings = SettingsManager()


class Transcribe:
    def __init__(self, translate: bool = False):

        self.translate = translate
        self.ro = ResolveObjects()
        self.media_file = ""

    def render(self):
        """
        Render active timeline in Resolve
        """

        logger.info("[yellow]Starting Resolve render")
        core.notify("Squawk", "Starting Resolve render")

        self.media_file = self.ro.render_timeline(
            settings["paths"]["working_dir"], settings["render"]["render_preset"]
        )
        logger.info("[green]Finished rendering")
        core.notify("Squawk", "Finished rendering")

    def tts(self):

        if not self.media_file:
            raise ValueError(f"Media file has not been defined! Run render first.")

        core.notify("Squawk", "Starting transcription")

        model = whisper.load_model(settings["whisper"]["model"])
        start_time = time.time()

        if self.translate:
            result = model.transcribe(self.media_file, task="translate")
        else:
            result = model.transcribe(self.media_file)

        core.notify(
            "Squawk", f"Processing finished after {time.time() - start_time} seconds"
        )

        # save SRT file to previously selected target_dir
        self.srt_path = os.path.join(
            settings["whisper"]["model"], (os.path.basename(self.media_file) + ".srt")
        )
        with open(self.srt_path, "w", encoding="utf-8") as srt:
            whisper_utils.write_srt(result["segments"], file=srt)

    def import_srt(self):
        """
        Import SRT file into Resolve
        """

        logger.info(f"[cyan]Importing SRT file: '{self.srt_path}'")

        # TODO: Allow importing to custom nested folder path
        root_folder = self.ro.media_pool.GetRootFolder()
        self.ro.media_pool.SetCurrentFolder(root_folder)
        self.ro.media_pool.ImportMedia(self.media_file)

    def run(self):

        self.render
        self.tts
        self.import_srt
