import pathlib
from typing import Any, Optional
from pydantic import (
    BaseModel,
    BaseSettings,
    Field,
    ValidationError,
    validator,
)
import rtoml
from rich import print

# TODO: Fix typing for Punctuation rules

# TODO: Add validators

from squawk.settings.manager import settings
from squawk.settings import manager


class SplitByGap(BaseModel):
    """
    Split (in-place) any segment into multiple segments where the duration in between two words > [max_gap]
    """
    max_gap: float = Field(
        ...,
        description="The point between any two words greater than this value (seconds) will be split."
    )
    lock: bool = Field(
        ...,
        description="Whether to prevent future splits from altering changes made by this function."

    )


class SplitByPunctuation(BaseModel):
    """
    Split (in-place) any segment into multiple segments where the duration in between two words > [max_gap]
    """
    punctuation: list[Any] = Field(
        ...,
        description="Punctuation(s) to split segments by."

    )
    lock: bool = Field(
        ...,
        description="Whether to prevent future splits from altering changes made by this function."

    )


class SplitByLength(BaseModel):
    """
    Split (in-place) any segment into multiple segments where the duration in between two words > [max_gap]
    """
    max_chars: int = Field(
        ...,
        description="Maximum number of characters allowed in segment."

    )
    max_words: int = Field(
        ...,
        description="Maximum number of words allowed in segment."

    )
    force_len: bool = Field(
        ...,
        description="Maintain a relatively constant length for each segment"

    )
    lock: bool = Field(
        ...,
        description="Whether to prevent future splits/merges from altering changes made by this function."
    )


class MergeByGap(BaseModel):
    """
    Merge (in-place) any pair of adjacent segments if the duration in between the pair <= [min_gap]
    """
    min_gap: float = Field(
        ...,
        description="Any gaps below or equal to this value (seconds) will be merged."

    )
    max_words: int = Field(
        ...,
        description="Maximum number of words allowed."

    )
    is_sum_max: bool = Field(
        ...,
        description="Whether [max_words] and [max_chars] are applied to the merged segment "
                    "instead of the individual segments to be merged."

    )
    lock: bool = Field(
        ...,
        description="Whether to prevent future splits/merges from altering changes made by this function."

    )


class MergeByPunctuation(BaseModel):
    """
    Merge (in-place) any two segments that has specified punctuation(s) inbetween them
    """
    punctuation: list[Any] = Field(
        ...,
        description="Punctuation(s) to split segments by."

    )
    max_chars: int = Field(
        ...,
        description="Maximum number of characters allowed in segment."

    )
    max_words: int = Field(
        ...,
        description="Maximum number of words allowed."

    )
    is_sum_max: bool = Field(
        ...,
        description="Whether [max_words] and [max_chars] are applied to the merged segment "
                    "instead of the individual segments to be merged."

    )
    lock: bool = Field(
        ...,
        description="Whether to prevent future splits/merges from altering changes made by this function."

    )


class MergeAllSegments(BaseModel):
  """
  Merge all segments into one segment.
  """
  enabled: bool = Field(
      ...,
      description="Whether to merge all segments into one"
  )

pathlib.Path(manager.__file__).parent

rules_toml = pathlib.Path(settings.regrouping.custom_rules_filepath).expanduser()
rules = rtoml.load(rules_toml.read_text())

class RulesModel(BaseModel):
    list[SplitByGap, SplitByPunctuation, SplitByLength, MergeByGap, MergeAllSegments]

parsed_rules = RulesModel(rules)
print(parsed_rules)