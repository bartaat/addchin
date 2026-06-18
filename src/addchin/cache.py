"""Bundled pre-generated content cache and word lists."""

import json
from importlib.resources import files
from pathlib import Path

_cache = None


def cache_path() -> Path:
    return Path(str(files("addchin").joinpath("data", "cache", "cards.json")))


def _load() -> dict:
    global _cache
    if _cache is None:
        _cache = json.loads(cache_path().read_text(encoding="utf-8"))
    return _cache


def lookup(word: str):
    """Return pre-generated language fields for `word`, or None."""
    return _load().get(word)


def _lists_dir() -> Path:
    return Path(str(files("addchin").joinpath("data", "lists")))


def available_lists() -> list:
    return sorted(p.stem for p in _lists_dir().glob("*.txt"))


def read_list(name: str) -> list:
    text = (_lists_dir() / f"{name}.txt").read_text(encoding="utf-8")
    return [w.strip() for w in text.splitlines() if w.strip()]
