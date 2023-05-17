from __future__ import annotations

import logging
import os
import pathlib
import re
import shutil

import rich.traceback
import rtoml
from pydantic import (
    BaseModel,
    BaseSettings,
    Field,
    ValidationError,
    validator,
)
from pydantic.env_settings import SettingsSourceCallable
from rich import print
from rich.panel import Panel

from squawk.settings import regrouping_rules

from squawk.settings import dotenv_settings_file, default_settings_file, user_settings_file

logger = logging.getLogger("squawk")
rich.traceback.install(show_locals=False)


def load_toml_user(_):
    user_toml = pathlib.Path(user_settings_file)
    return rtoml.load(user_toml.read_text())


class App(BaseModel):
    loglevel: str = Field("WARNING", description="General application loglevel")
    check_for_updates: bool = Field(
        True, description="Enable/Disable checking for updates"
    )
    update_check_url: str = Field(
        ...,
        description="URL to check for app updates from"
    )
    subtitle_folder_path: str = Field(
        ..., 
        description="Create and import the subtitles into this folder structure in Resolve's media pool",

    )
    working_dir: str = Field(
        ..., 
        description="Where to store transcription working files",

    )
    
    @validator("loglevel")
    def must_be_valid_loglevel(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v not in valid_levels:
            raise ValueError(
                f"'{v}' is not a valid loglevel. Choose from [cyan]{', '.join(valid_levels)}[/]"
            )
        return v
    
    @validator("working_dir",)
    def ensure_path(cls, v):
        if not os.path.exists(v):
            try: 
                os.makedirs(v)
            except PermissionError:
                raise ValueError(
                    f"Path {v} does not exist and "
                    "insufficient permissions to create"
                )
        return v


class TextToSpeech(BaseModel):
    model: str = Field(
        ..., description="The Whisper model to download and use for transcription"
    )
    translate_to_english: bool = Field(
        ..., description="Whether or not to translate the transcription"
    )


class Regrouping(BaseModel):
    enabled: bool = Field(
        ...,
        description="Whether to enable transcription regrouping rules"
    )
    
    # Regrouping rules defined in separate module
    split_by_gap: regrouping_rules.SplitByGap
    split_by_punctuation: regrouping_rules.SplitByPunctuation
    split_by_length: regrouping_rules.SplitByLength
    merge_by_gap: regrouping_rules.MergeByGap
    merge_by_punctuation: regrouping_rules.MergeByPunctuation
    merge_all_segments: regrouping_rules.MergeAllSegments
    

class Settings(BaseSettings):
    app: App
    text_to_speech: TextToSpeech
    regrouping: Regrouping

    class Config:
        env_file = dotenv_settings_file
        env_file_encoding = "utf-8"
        env_prefix = "SQUAWK_"
        env_nested_delimiter = "__"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ) -> tuple[SettingsSourceCallable, ...]:
            return (
                env_settings,
                load_toml_user,
                file_secret_settings,
                init_settings,
            )


settings = None

# Ensure user settings are accessible
if not os.path.exists(user_settings_file):
    logger.warning("[yellow]Initalising user settings file...")
    try:
        shutil.copy(default_settings_file, user_settings_file)
    except PermissionError as e:
        logger.error("Couldn't initialise user settings file! Invalid permi")

try:
    settings = Settings()

except ValidationError as e:
    print(
        Panel(
            title="[red]Uh, oh! Invalid user settings",
            title_align="left",
            highlight=True,
            expand=False,
            renderable=f"\n{str(e)}\n\nRun 'Proxima config --help' to see how to fix broken settings.",
        )
    )

if __name__ == "__main__":
    if settings:
        print(settings.dict())
