"""Local, free conversions: traditional, pinyin, and TTS audio."""

import asyncio
import tempfile
from pathlib import Path

import edge_tts
from opencc import OpenCC
from pypinyin import Style, pinyin

_cc = OpenCC("s2t")  # simplified -> traditional


def to_traditional(text: str) -> str:
    return _cc.convert(text)


def to_pinyin(text: str) -> str:
    """Space-separated pinyin with tone marks, e.g. 'péng yǒu'."""
    return " ".join(syll[0] for syll in pinyin(text, style=Style.TONE))
