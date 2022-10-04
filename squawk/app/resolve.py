import imp
import logging
import os
import pathlib
import sys
from datetime import datetime

from rich import traceback

from squawk import exceptions
from squawk.settings import SettingsManager
from squawk.utils import core

settings = SettingsManager()

traceback.install()
logger = logging.getLogger(__name__)
logger.setLevel(settings["app"]["loglevel"])


class ResolveObjects:
    def __init__(self):

        self.resolve = self.__get_resolve()

        if self.resolve is None:
            raise exceptions.ResolveAPIConnectionError()

        self.project = self.resolve.GetProjectManager().GetCurrentProject()
        if self.project is None:
            raise exceptions.ResolveNoCurrentProjectError()

        self.timeline = self.project.GetCurrentTimeline()
        if self.timeline is None:
            raise exceptions.ResolveNoCurrentTimelineError()

        self.media_pool = self.project.GetMediaPool()
        if self.media_pool is None:
            raise exceptions.ResolveNoMediaPoolError()

    def __get_resolve(self):

        ext = ".so"
        if sys.platform.startswith("darwin"):
            path = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/"
        elif sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
            path = "C:\\Program Files\\Blackmagic Design\\DaVinci Resolve\\"
            ext = ".dll"
        elif sys.platform.startswith("linux"):
            path = "/opt/resolve/libs/Fusion/"
        else:
            raise exceptions.ResolveUnsupportedPlatform(
                "Unsupported system! " + sys.platform
            )

        bmd = imp.load_dynamic("fusionscript", path + "fusionscript" + ext)
        resolve = bmd.scriptapp("Resolve")

        if not resolve:
            return None

        try:
            sys.modules[__name__] = resolve
        except ImportError:
            return None

        return resolve

    def get_video_track_items(self, timeline):
        """Get all video track items from the provided timeline"""

        all_track_items = []

        # Get count of tracks (index) in active timeline
        track_len = timeline.GetTrackCount("video")
        logger.info(f"[green]Video track count: {track_len}[/]")

        # For each track in timeline (using index)
        for i in range(1, track_len + 1):

            # Get items
            track_items = timeline.GetItemListInTrack("video", i)

            if track_items is None:
                logger.debug(f"[magenta]No items found in track {i}[/]")
                continue

            else:
                all_track_items.append(track_items)

        return all_track_items

    def get_media_pool_items(self, track_items):
        """Return media pool items for all track items"""

        all_media_pool_items = []

        for track in track_items:
            for item in track:
                media_item = item.GetMediaPoolItem()
                all_media_pool_items.append(media_item)

        return all_media_pool_items

    def get_resolve_timelines(self, project, active_timeline_first=True):
        """Return a list of all Resolve timeline objects in current project."""

        timelines = []

        timeline_len = project.GetTimelineCount()
        if timeline_len > 0:

            for i in range(1, timeline_len + 1):
                timeline = project.GetTimelineByIndex(i)
                timelines.append(timeline)

            if active_timeline_first:
                active = project.GetCurrentTimeline().GetName()  # Get active timeline
                timeline_names = [x.GetName() for x in timelines]
                active_i = timeline_names.index(
                    active
                )  # It's already in the list, find it's index
                timelines.insert(
                    0, timelines.pop(active_i)
                )  # Move it to the front, indexing should be the same as name list
        else:
            return False

        return timelines

    def get_resolve_proxy_jobs(self, media_pool_items):
        """Return source metadata for each media pool item that passes configured criteria.

        each media pool item must meet the following criteria:
            - return valid clip properties (needed for encoding, internal track items don't have them)
            - whitelisted extension (e.g, BRAW performs fine without proxies)
            - whitelisted framerate (optional) FFmpeg should handle most

        Args:
            - media_pool_items: list of Resolve API media pool items

        Returns:
            - filtered_metadata: a list of dictionaries containing clip attributes for proxy-encodable Resolve media.

        Raises:
            - none

        """

        jobs = []
        seen = []

        for media_pool_item in media_pool_items:

            # Check media pool item is valid, get UUID
            try:

                mpi_uuid = str(media_pool_item).split("UUID:")[1].split("]")[0]
                logger.debug(f"[magenta]Media Pool Item: {mpi_uuid}")

            except:

                logger.debug(
                    f"[magenta]Media Pool Item: 'None'[/]\n"
                    + f"[yellow]Invalid item: has no UUID[/]\n"
                )
                continue

            if str(media_pool_item) in seen:

                logger.debug(
                    f"[magenta]Media Pool Item: {mpi_uuid}[/]\n"
                    + "[yellow]Already seen media pool item. Skipping...[/]\n"
                )
                continue

            else:

                # Add first encounter to list for comparison
                seen.append(str(media_pool_item))

            # Check media pool item has clip properties
            if not hasattr(media_pool_item, "GetClipProperty()"):

                logger.debug(
                    f"[magenta]Media Pool Item: {mpi_uuid}[/]\n"
                    + "[yellow]Media pool item has no clip properties. Skipping...[/]\n"
                )
                continue

            # Get source metadata, path, extension
            clip_properties = media_pool_item.GetClipProperty()
            source_path = clip_properties["File Path"]
            source_ext = os.path.splitext(source_path)[1].lower()

            # Might still get media that has clip properties, but empty attributes
            # Should only be internally generated media that returns this way
            if source_path == "":

                logger.debug(
                    f"[magenta]Media Pool Item: {mpi_uuid}[/]\n"
                    + f"clip properties did not return a valid filepath. Skipping...\n"
                )
                continue

            # Filter extension
            if settings["filters"]["extension_whitelist"]:

                if source_ext not in settings["filters"]["extension_whitelist"]:

                    logger.warning(
                        f"[yellow]Ignoring file with extension not in whitelist: '{source_ext}'\n"
                        + f"from '{clip_properties['File Path']}'[/]\n"
                    )
                    continue

            # Filter framerate
            if settings["filters"]["framerate_whitelist"]:

                # Make int to avoid awkward extra zeros.
                if float(clip_properties["FPS"]).is_integer():
                    clip_properties["FPS"] = int(float(clip_properties["FPS"]))

                if (
                    clip_properties["FPS"]
                    not in settings["filters"]["framerate_whitelist"]
                ):

                    logger.warning(
                        f"[yellow]Ignoring file with framerate not in whitelist: '{clip_properties['FPS']}'\n"
                        + f"from '{clip_properties['File Path']}' [/]\n"
                    )
                    continue

            # Get expected proxy path
            file_path = clip_properties["File Path"]
            p = pathlib.Path(file_path)

            proxy_dir = os.path.normpath(
                os.path.join(
                    settings["paths"]["proxy_path_root"],
                    os.path.dirname(p.relative_to(*p.parts[:1])),
                )
            )

            # TODO: These would definitely be nicer as class attributes
            # labels: enhancement
            cp = clip_properties
            job = {
                "clip_name": cp["Clip Name"],
                "file_name": cp["File Name"],
                "file_path": cp["File Path"],
                "duration": cp["Duration"],
                "data_level": cp["Data Level"],
                "resolution": str(cp["Resolution"]).split("x"),
                "frames": int(cp["Frames"]),
                "fps": float(cp["FPS"]),
                "h_flip": True if cp["H-FLIP"] == "On" else False,
                "v_flip": True if cp["H-FLIP"] == "On" else False,
                "proxy_status": cp["Proxy"],
                "proxy_media_path": cp["Proxy Media Path"]
                if not len(cp["Proxy Media Path"])
                else cp["Proxy Media Path"],
                "proxy_dir": proxy_dir,
                "start": int(cp["Start"]),
                "end": int(cp["End"]),
                "start_tc": cp["Start TC"],
                "end_tc": cp["End TC"],
                "media_pool_item": media_pool_item,
            }

            logger.debug(f"[magenta]Clip properties: {job}\n")
            jobs.append(job)

        logger.info(f"[green]Total queuable clips on timeline: {len(jobs)}[/]")

        return jobs

    def render_timeline(self, output_path: str, render_preset: str):

        # get the available render presets
        valid_presets = self.project.GetRenderPresetList()

        if not render_preset in valid_presets:
            raise exceptions.ResolveInvalidRenderPresetError(render_preset)

        if not self.project.LoadRenderPreset(render_preset):
            logger.error(f"[red]Could not set render preset: {render_preset}")
            core.app_exit(1, 1)

        renderSettings = dict(
            MarkIn=self.timeline.GetStartFrame(),
            MarkOut=self.timeline.GetEndFrame(),
            CustomName=f"{self.project.GetName()} - {self.timeline.GetName()} - {datetime.now()}",
        )

        self.project.SetRenderSettings(renderSettings)
        render_job_id = self.project.AddRenderJob()
        self.project.StartRendering(render_job_id)
        self.project.GetRenderJobStatus(render_job_id)
