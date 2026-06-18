"""Generate language fields via the Anthropic API or the claude CLI."""

import json
import os
import shutil
import subprocess

import anthropic

from . import config

_KEYS = ("meaning", "pos", "sentence", "sentence_meaning")

_PROMPT = """You are building an Anki flashcard for a beginner studying Mandarin.
For the simplified-Chinese word: {word}

Return ONLY a JSON object (no markdown, no code fences, no commentary) with exactly these keys:
  "meaning": a concise English definition suitable for a flashcard (a few words, not a paragraph)
  "pos": the part of speech (e.g. "noun", "verb", "adjective", "measure word")
  "sentence": a short, natural example sentence in SIMPLIFIED Chinese that uses {word}, suitable for a beginner (HSK1-3 vocabulary where possible)
  "sentence_meaning": a natural English translation of that sentence

Do not include pinyin or traditional characters; those are added separately."""

_SCHEMA = {
    "type": "object",
    "properties": {
        "meaning": {"type": "string"},
        "pos": {"type": "string"},
        "sentence": {"type": "string"},
        "sentence_meaning": {"type": "string"},
    },
    "required": list(_KEYS),
    "additionalProperties": False,
}


def _validate(data: dict) -> dict:
    for key in _KEYS:
        data.setdefault(key, "")
    return {key: data[key] for key in _KEYS}


def _generate_api(word: str, model: str) -> dict:
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model or config.DEFAULT_LLM_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": _PROMPT.format(word=word)}],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
    )
    text = next(b.text for b in resp.content if b.type == "text")
    return _validate(json.loads(text))


def _generate_cli(word: str, model: str) -> dict:
    cmd = ["claude", "-p", _PROMPT.format(word=word)]
    if model:
        cmd += ["--model", model]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {proc.stderr.strip()}")
    raw = proc.stdout.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return _validate(json.loads(raw))


def generate(word: str, model: str = None) -> dict:
    """Return language fields for `word`. Prefers the API key, else the claude CLI."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _generate_api(word, model)
    if shutil.which("claude"):
        return _generate_cli(word, model)
    raise RuntimeError(
        "No LLM backend available. Set ANTHROPIC_API_KEY or install the Claude CLI "
        "(https://claude.com/claude-code)."
    )
