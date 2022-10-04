import re
from commonregex import link
import os
from schema import Schema, And, Optional


settings_schema = Schema(
    {
        "app": {
            "loglevel": lambda s: s
            in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "check_for_updates": bool,
            "update_check_url": lambda s: re.match(link, s),
        },
        "paths": {
            "working_dir": lambda p: os.path.exists(p),
        },
        "resolve": {
            "render_preset": str,
            "subtitle_folder_path": str,
        },
        "text_to_speech": {
            "model": lambda s: s in ["tiny", "small", "medium", "large"],
        },
    },
    ignore_extra_keys=True,
)
