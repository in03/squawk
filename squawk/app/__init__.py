import logging

from rich import traceback
from rich.logging import RichHandler

# Rich traceback and logger

traceback.install()

def setup_rich_logging():

    """Set logger to rich, allowing for console markup."""

    FORMAT = "%(message)s"
    logging.basicConfig(
        level="WARNING",
        format=FORMAT,
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                tracebacks_extra_lines=1,
                markup=True,
            )
        ],
    )


setup_rich_logging()
logger = logging.getLogger("squawk")