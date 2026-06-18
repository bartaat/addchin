"""Prerequisite checks for `addchin --check`."""

import os
import shutil

from . import anki, config


def _print(ok: bool, label: str, hint: str = "") -> None:
    mark = "OK  " if ok else "FAIL"
    line = f"[{mark}] {label}"
    if not ok and hint:
        line += f"\n       -> {hint}"
    print(line)


def check() -> bool:
    try:
        anki.invoke("version")
        anki_ok = True
    except anki.AnkiError:
        anki_ok = False
    _print(
        anki_ok,
        "AnkiConnect reachable",
        f"Open Anki and install the AnkiConnect add-on (code {config.ANKI_ADDON_CODE}).",
    )

    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_cli = shutil.which("claude") is not None
    backend_ok = has_key or has_cli
    _print(
        backend_ok,
        "LLM backend available",
        "Set ANTHROPIC_API_KEY or install the Claude CLI (only needed for words not in the cache).",
    )

    return anki_ok and backend_ok
