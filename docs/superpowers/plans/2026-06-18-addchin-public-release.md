# addchin Public Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the single-file `generate_cards.py` into an installable, self-configuring `addchin` package that builds Anki Mandarin cards from words, files, or bundled lists.

**Architecture:** Small Python package under `src/addchin/` with focused modules. Per word: look up pre-generated language fields in a committed cache first (free), else call Claude (Anthropic API key, else `claude` CLI); then add traditional/pinyin/audio locally; then insert via AnkiConnect, auto-creating the deck and a self-contained note type.

**Tech Stack:** Python 3.9+, `anthropic`, `requests`, `pypinyin`, `opencc-python-reimplemented`, `edge-tts`; `pytest`; build backend `hatchling`; `uv` for the installer.

## Global Constraints

- Package source lives under `src/addchin/`; tests under `tests/`.
- Console entry point: `addchin = "addchin.cli:main"`.
- Default deck **and** note type name: `Addchin Mandarin`.
- Default voice: `zh-CN-XiaoxiaoNeural`. Default LLM model: `claude-opus-4-8`.
- AnkiConnect URL: `http://localhost:8765`; AnkiConnect add-on code: `2055492159`.
- Cache file: `src/addchin/data/cache/cards.json`, a map `word -> {meaning, pos, sentence, sentence_meaning}`.
- Bundled lists: `src/addchin/data/lists/<name>.txt`, one simplified word per line.
- Tests must not touch the network: mock `requests`, `anthropic`, `edge_tts`, and `subprocess`.
- `anthropic>=0.40` is the declared floor; the API path uses `output_config.format` (structured outputs) — if the installed SDK rejects `output_config`, bump the floor. Verify with `pip show anthropic`.
- Commit after every task with the shown message.

---

### Task 1: Project scaffold + config

**Files:**
- Create: `pyproject.toml`
- Create: `src/addchin/__init__.py`
- Create: `src/addchin/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `addchin.config` module with constants `ANKI_URL: str`, `ANKI_ADDON_CODE: str`, `DEFAULT_DECK: str`, `DEFAULT_NOTE_TYPE: str`, `DEFAULT_VOICE: str`, `DEFAULT_LLM_MODEL: str`, `DEFAULT_TAGS: list[str]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
from addchin import config


def test_defaults():
    assert config.ANKI_URL == "http://localhost:8765"
    assert config.ANKI_ADDON_CODE == "2055492159"
    assert config.DEFAULT_DECK == "Addchin Mandarin"
    assert config.DEFAULT_NOTE_TYPE == "Addchin Mandarin"
    assert config.DEFAULT_VOICE == "zh-CN-XiaoxiaoNeural"
    assert config.DEFAULT_LLM_MODEL == "claude-opus-4-8"
    assert config.DEFAULT_TAGS == ["addchin"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv venv && uv pip install -e ".[dev]"` then `uv run pytest tests/test_config.py -v`
Expected: FAIL — `pyproject.toml`/package does not exist yet (install or import error).

- [ ] **Step 3: Create the scaffold and config**

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "addchin"
version = "0.1.0"
description = "Turn a list of Chinese words into fully-formed Anki flashcards."
readme = "README.md"
requires-python = ">=3.9"
license = { text = "MIT" }
dependencies = [
    "anthropic>=0.40",
    "requests>=2.28",
    "pypinyin>=0.49",
    "opencc-python-reimplemented>=0.1.7",
    "edge-tts>=6.1",
]

[project.optional-dependencies]
dev = ["pytest>=7"]

[project.scripts]
addchin = "addchin.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/addchin"]
```

```python
# src/addchin/__init__.py
"""addchin — build Anki Mandarin cards from a word list."""

__version__ = "0.1.0"
```

```python
# src/addchin/config.py
"""Defaults and constants. No logic."""

ANKI_URL = "http://localhost:8765"
ANKI_ADDON_CODE = "2055492159"

DEFAULT_DECK = "Addchin Mandarin"
DEFAULT_NOTE_TYPE = "Addchin Mandarin"
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
DEFAULT_LLM_MODEL = "claude-opus-4-8"
DEFAULT_TAGS = ["addchin"]
```

Create an empty `README.md` so the build has its declared readme:

```bash
printf '# addchin\n' > README.md
```

- [ ] **Step 4: Install and run the test**

Run: `uv pip install -e ".[dev]" && uv run pytest tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md src/addchin/__init__.py src/addchin/config.py tests/test_config.py
git commit -m "feat: scaffold addchin package and config defaults"
```

---

### Task 2: Chinese text conversion (pinyin + traditional)

**Files:**
- Create: `src/addchin/chinese.py`
- Test: `tests/test_chinese.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `chinese.to_traditional(text: str) -> str`, `chinese.to_pinyin(text: str) -> str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_chinese.py
from addchin import chinese


def test_to_traditional():
    assert chinese.to_traditional("图书馆") == "圖書館"


def test_to_pinyin():
    assert chinese.to_pinyin("朋友") == "péng yǒu"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_chinese.py -v`
Expected: FAIL — `No module named 'addchin.chinese'`.

- [ ] **Step 3: Implement conversions**

```python
# src/addchin/chinese.py
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
```

- [ ] **Step 4: Run the test**

Run: `uv run pytest tests/test_chinese.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/addchin/chinese.py tests/test_chinese.py
git commit -m "feat: add traditional and pinyin conversion"
```

---

### Task 3: TTS audio bytes

**Files:**
- Modify: `src/addchin/chinese.py`
- Test: `tests/test_chinese_audio.py`

**Interfaces:**
- Consumes: `edge_tts` (already imported in Task 2).
- Produces: `chinese.make_audio(text: str, voice: str) -> bytes` (the mp3 bytes).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_chinese_audio.py
from pathlib import Path

from addchin import chinese


class _FakeCommunicate:
    def __init__(self, text, voice):
        self.text = text

    async def save(self, path):
        Path(path).write_bytes(b"ID3-fake-" + self.text.encode("utf-8"))


def test_make_audio_returns_bytes(monkeypatch):
    monkeypatch.setattr(chinese.edge_tts, "Communicate", _FakeCommunicate)
    data = chinese.make_audio("你好", "zh-CN-XiaoxiaoNeural")
    assert isinstance(data, bytes)
    assert data.startswith(b"ID3-fake-")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_chinese_audio.py -v`
Expected: FAIL — `module 'addchin.chinese' has no attribute 'make_audio'`.

- [ ] **Step 3: Add `make_audio`**

Append to `src/addchin/chinese.py`:

```python
def make_audio(text: str, voice: str) -> bytes:
    """Synthesize `text` with edge-tts and return mp3 bytes."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "out.mp3"
        asyncio.run(edge_tts.Communicate(text, voice).save(str(path)))
        return path.read_bytes()
```

- [ ] **Step 4: Run the test**

Run: `uv run pytest tests/test_chinese_audio.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/addchin/chinese.py tests/test_chinese_audio.py
git commit -m "feat: add edge-tts audio synthesis"
```

---

### Task 4: Content cache + bundled lists

**Files:**
- Create: `src/addchin/cache.py`
- Create: `src/addchin/data/cache/cards.json`
- Create: `src/addchin/data/lists/hsk1.txt`
- Test: `tests/test_cache.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `cache.lookup(word: str) -> dict | None`, `cache.available_lists() -> list[str]`, `cache.read_list(name: str) -> list[str]`, `cache.cache_path() -> pathlib.Path`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cache.py
from addchin import cache


def test_lookup_hit():
    entry = cache.lookup("朋友")
    assert entry is not None
    assert set(entry) == {"meaning", "pos", "sentence", "sentence_meaning"}


def test_lookup_miss():
    assert cache.lookup("没有这个词xyz") is None


def test_lists():
    assert "hsk1" in cache.available_lists()
    words = cache.read_list("hsk1")
    assert "朋友" in words
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache.py -v`
Expected: FAIL — `No module named 'addchin.cache'`.

- [ ] **Step 3: Create data files and the cache module**

```json
// src/addchin/data/cache/cards.json
{
  "朋友": {
    "meaning": "friend",
    "pos": "noun",
    "sentence": "我有很多朋友。",
    "sentence_meaning": "I have many friends."
  },
  "图书馆": {
    "meaning": "library",
    "pos": "noun",
    "sentence": "我去图书馆看书。",
    "sentence_meaning": "I go to the library to read."
  },
  "喜欢": {
    "meaning": "to like",
    "pos": "verb",
    "sentence": "我喜欢喝茶。",
    "sentence_meaning": "I like drinking tea."
  },
  "觉得": {
    "meaning": "to think; to feel",
    "pos": "verb",
    "sentence": "我觉得这个很好。",
    "sentence_meaning": "I think this is very good."
  }
}
```

```
朋友
图书馆
喜欢
觉得
```
(Save the four lines above as `src/addchin/data/lists/hsk1.txt`.)

```python
# src/addchin/cache.py
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
```

- [ ] **Step 4: Run the test**

Run: `uv run pytest tests/test_cache.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/addchin/cache.py src/addchin/data/cache/cards.json src/addchin/data/lists/hsk1.txt tests/test_cache.py
git commit -m "feat: add content cache and bundled hsk1 list"
```

---

### Task 5: Note-type definition (fields + card templates + CSS)

**Files:**
- Create: `src/addchin/templates.py`
- Test: `tests/test_templates.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `templates.NOTE_TYPE_FIELDS: list[str]`, `templates.model_spec(model_name: str) -> dict` (a valid AnkiConnect `createModel` payload).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_templates.py
from addchin import templates


def test_fields_present():
    for field in ("Simplified", "Pinyin", "Meaning", "Audio", "SentenceSimplified", "Notes"):
        assert field in templates.NOTE_TYPE_FIELDS


def test_model_spec_shape():
    spec = templates.model_spec("Addchin Mandarin")
    assert spec["modelName"] == "Addchin Mandarin"
    assert spec["inOrderFields"] == templates.NOTE_TYPE_FIELDS
    assert spec["css"].strip() != ""
    card = spec["cardTemplates"][0]
    assert "{{Simplified}}" in card["Front"]
    assert "{{Meaning}}" in card["Back"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_templates.py -v`
Expected: FAIL — `No module named 'addchin.templates'`.

- [ ] **Step 3: Implement the templates**

```python
# src/addchin/templates.py
"""The self-contained "Addchin Mandarin" note type."""

NOTE_TYPE_FIELDS = [
    "Simplified",
    "Traditional",
    "Pinyin",
    "Meaning",
    "PartOfSpeech",
    "Audio",
    "SentenceSimplified",
    "SentenceTraditional",
    "SentencePinyin",
    "SentenceMeaning",
    "SentenceAudio",
    "Notes",
]

_FRONT = """<div class="hanzi">{{Simplified}}</div>
{{Audio}}"""

_BACK = """{{FrontSide}}
<hr id="answer">
<div class="pinyin">{{Pinyin}}</div>
<div class="meaning">{{Meaning}} <span class="pos">{{PartOfSpeech}}</span></div>
<div class="traditional">繁體 {{Traditional}}</div>
<div class="sentence">{{SentenceSimplified}}</div>
<div class="sentence-pinyin">{{SentencePinyin}}</div>
<div class="sentence-meaning">{{SentenceMeaning}}</div>
{{SentenceAudio}}
<div class="notes">{{Notes}}</div>"""

_CSS = """.card {
  font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
  font-size: 20px;
  text-align: center;
  color: #1a1a1a;
  background: #fbfbfb;
}
.hanzi { font-size: 64px; margin: 24px 0; }
.pinyin { font-size: 26px; color: #c0392b; margin-top: 12px; }
.meaning { font-size: 24px; margin: 8px 0; }
.pos { font-size: 16px; color: #888; }
.traditional { font-size: 16px; color: #888; margin-bottom: 16px; }
.sentence { font-size: 24px; margin-top: 16px; }
.sentence-pinyin { font-size: 18px; color: #c0392b; }
.sentence-meaning { font-size: 18px; color: #555; }
.notes { font-size: 14px; color: #999; margin-top: 16px; }
hr#answer { margin: 20px 0; }"""


def model_spec(model_name: str) -> dict:
    """Return an AnkiConnect `createModel` payload for the note type."""
    return {
        "modelName": model_name,
        "inOrderFields": NOTE_TYPE_FIELDS,
        "css": _CSS,
        "isCloze": False,
        "cardTemplates": [
            {"Name": "Recognition", "Front": _FRONT, "Back": _BACK}
        ],
    }
```

- [ ] **Step 4: Run the test**

Run: `uv run pytest tests/test_templates.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/addchin/templates.py tests/test_templates.py
git commit -m "feat: add Addchin Mandarin note-type definition"
```

---

### Task 6: AnkiConnect client

**Files:**
- Create: `src/addchin/anki.py`
- Test: `tests/test_anki.py`

**Interfaces:**
- Consumes: `config.ANKI_URL`, `templates.model_spec`.
- Produces: `anki.AnkiError` (exception), `anki.invoke(action, **params)`, `anki.ensure_deck(deck: str)`, `anki.ensure_note_type(note_type: str)`, `anki.store_media(filename: str, data: bytes)`, `anki.add_note(deck, note_type, fields: dict, tags: list) -> int`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_anki.py
import pytest
import requests

from addchin import anki


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_invoke_returns_result(monkeypatch):
    monkeypatch.setattr(anki.requests, "post", lambda *a, **k: _FakeResp({"result": 6, "error": None}))
    assert anki.invoke("version") == 6


def test_invoke_raises_on_error(monkeypatch):
    monkeypatch.setattr(anki.requests, "post", lambda *a, **k: _FakeResp({"result": None, "error": "boom"}))
    with pytest.raises(anki.AnkiError):
        anki.invoke("addNote")


def test_invoke_raises_when_unreachable(monkeypatch):
    def _boom(*a, **k):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(anki.requests, "post", _boom)
    with pytest.raises(anki.AnkiError):
        anki.invoke("version")


def test_ensure_note_type_creates_when_missing(monkeypatch):
    calls = []

    def fake_invoke(action, **params):
        calls.append((action, params))
        return [] if action == "modelNames" else None

    monkeypatch.setattr(anki, "invoke", fake_invoke)
    anki.ensure_note_type("Addchin Mandarin")
    assert [c[0] for c in calls] == ["modelNames", "createModel"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_anki.py -v`
Expected: FAIL — `No module named 'addchin.anki'`.

- [ ] **Step 3: Implement the client**

```python
# src/addchin/anki.py
"""AnkiConnect client: deck/note-type creation, media, and notes."""

import base64

import requests

from . import config, templates


class AnkiError(RuntimeError):
    pass


def invoke(action: str, **params):
    body = {"action": action, "version": 6, "params": params}
    try:
        resp = requests.post(config.ANKI_URL, json=body, timeout=30)
    except requests.exceptions.RequestException as exc:
        raise AnkiError(
            f"Could not reach AnkiConnect at {config.ANKI_URL}. "
            f"Open Anki and install the AnkiConnect add-on (code {config.ANKI_ADDON_CODE})."
        ) from exc
    payload = resp.json()
    if payload.get("error") is not None:
        raise AnkiError(f"AnkiConnect error on {action}: {payload['error']}")
    return payload["result"]


def ensure_deck(deck: str) -> None:
    invoke("createDeck", deck=deck)


def ensure_note_type(note_type: str) -> None:
    if note_type not in invoke("modelNames"):
        invoke("createModel", **templates.model_spec(note_type))


def store_media(filename: str, data: bytes) -> None:
    invoke("storeMediaFile", filename=filename, data=base64.b64encode(data).decode("ascii"))


def add_note(deck: str, note_type: str, fields: dict, tags: list) -> int:
    note = {
        "deckName": deck,
        "modelName": note_type,
        "fields": fields,
        "tags": tags,
        "options": {"allowDuplicate": False, "duplicateScope": "deck"},
    }
    return invoke("addNote", note=note)
```

- [ ] **Step 4: Run the test**

Run: `uv run pytest tests/test_anki.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/addchin/anki.py tests/test_anki.py
git commit -m "feat: add AnkiConnect client with auto deck/note-type creation"
```

---

### Task 7: LLM backend (API key, else claude CLI)

**Files:**
- Create: `src/addchin/llm.py`
- Test: `tests/test_llm.py`

**Interfaces:**
- Consumes: `config.DEFAULT_LLM_MODEL`.
- Produces: `llm.generate(word: str, model: str | None = None) -> dict` returning exactly the keys `meaning, pos, sentence, sentence_meaning`. Internal helpers `llm._generate_api(word, model)`, `llm._generate_cli(word, model)`, `llm._validate(data)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm.py
import pytest

from addchin import llm


class _Block:
    type = "text"
    text = '{"meaning":"friend","pos":"noun","sentence":"我有朋友。","sentence_meaning":"I have friends."}'


class _Resp:
    content = [_Block()]


class _Client:
    class messages:
        @staticmethod
        def create(**kwargs):
            return _Resp()


def test_validate_fills_missing():
    out = llm._validate({"meaning": "x"})
    assert set(out) == {"meaning", "pos", "sentence", "sentence_meaning"}
    assert out["pos"] == ""


def test_generate_uses_api_when_key_present(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(llm.anthropic, "Anthropic", lambda: _Client())
    out = llm.generate("朋友")
    assert out["meaning"] == "friend"


def test_generate_uses_cli_when_no_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(llm.shutil, "which", lambda name: "/usr/bin/claude")

    class _Proc:
        returncode = 0
        stdout = '{"meaning":"library","pos":"noun","sentence":"x","sentence_meaning":"y"}'
        stderr = ""

    monkeypatch.setattr(llm.subprocess, "run", lambda *a, **k: _Proc())
    out = llm.generate("图书馆")
    assert out["meaning"] == "library"


def test_generate_raises_when_no_backend(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(llm.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError):
        llm.generate("朋友")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_llm.py -v`
Expected: FAIL — `No module named 'addchin.llm'`.

- [ ] **Step 3: Implement the backend**

```python
# src/addchin/llm.py
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
```

- [ ] **Step 4: Run the test**

Run: `uv run pytest tests/test_llm.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/addchin/llm.py tests/test_llm.py
git commit -m "feat: add dual LLM backend (API key, else claude CLI)"
```

---

### Task 8: Doctor (`--check`)

**Files:**
- Create: `src/addchin/doctor.py`
- Test: `tests/test_doctor.py`

**Interfaces:**
- Consumes: `anki.invoke`, `anki.AnkiError`.
- Produces: `doctor.check() -> bool` (prints a checklist; returns True only if Anki/AnkiConnect is reachable AND an LLM backend is available).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_doctor.py
from addchin import doctor


def test_check_all_ok(monkeypatch, capsys):
    monkeypatch.setattr(doctor.anki, "invoke", lambda action, **k: 6)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    assert doctor.check() is True
    out = capsys.readouterr().out
    assert "AnkiConnect" in out


def test_check_anki_down(monkeypatch):
    def _boom(action, **k):
        raise doctor.anki.AnkiError("down")

    monkeypatch.setattr(doctor.anki, "invoke", _boom)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    assert doctor.check() is False


def test_check_no_backend(monkeypatch):
    monkeypatch.setattr(doctor.anki, "invoke", lambda action, **k: 6)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)
    assert doctor.check() is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_doctor.py -v`
Expected: FAIL — `No module named 'addchin.doctor'`.

- [ ] **Step 3: Implement the doctor**

```python
# src/addchin/doctor.py
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
```

- [ ] **Step 4: Run the test**

Run: `uv run pytest tests/test_doctor.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/addchin/doctor.py tests/test_doctor.py
git commit -m "feat: add prerequisite doctor check"
```

---

### Task 9: CLI parser, word resolution, and text fields

**Files:**
- Create: `src/addchin/cli.py`
- Test: `tests/test_cli_fields.py`

**Interfaces:**
- Consumes: `config`, `cache`, `llm`, `chinese`.
- Produces: `cli.build_parser() -> argparse.ArgumentParser`, `cli.resolve_words(args) -> list[str]`, `cli.card_text_fields(word: str, args) -> dict` (all 12 note fields; `Audio`/`SentenceAudio`/`Notes` empty here). `resolve_words` raises `SystemExit` (via `parser.error`) when no single source is given.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli_fields.py
import pytest

from addchin import cli


def _args(**over):
    parser = cli.build_parser()
    argv = over.pop("argv", [])
    ns = parser.parse_args(argv)
    for key, value in over.items():
        setattr(ns, key, value)
    return ns


def test_card_text_fields_uses_cache(monkeypatch):
    monkeypatch.setattr(
        cli.cache, "lookup",
        lambda w: {"meaning": "friend", "pos": "noun", "sentence": "我有朋友。", "sentence_meaning": "I have friends."},
    )
    called = []
    monkeypatch.setattr(cli.llm, "generate", lambda w, m: called.append(w) or {})
    fields = cli.card_text_fields("朋友", _args(argv=["朋友"]))
    assert fields["Simplified"] == "朋友"
    assert fields["Meaning"] == "friend"
    assert fields["Pinyin"] == "péng yǒu"
    assert fields["SentenceTraditional"] == "我有朋友。"  # unchanged: no traditional variants here
    assert fields["Audio"] == ""
    assert called == []  # cache hit -> no LLM


def test_card_text_fields_regenerate_calls_llm(monkeypatch):
    monkeypatch.setattr(cli.cache, "lookup", lambda w: {"meaning": "STALE", "pos": "", "sentence": "", "sentence_meaning": ""})
    monkeypatch.setattr(
        cli.llm, "generate",
        lambda w, m: {"meaning": "fresh", "pos": "noun", "sentence": "", "sentence_meaning": ""},
    )
    fields = cli.card_text_fields("朋友", _args(argv=["朋友"], regenerate=True))
    assert fields["Meaning"] == "fresh"


def test_resolve_words_from_list(monkeypatch):
    monkeypatch.setattr(cli.cache, "read_list", lambda name: ["朋友", "喜欢"])
    assert cli.resolve_words(_args(argv=["--list", "hsk1"])) == ["朋友", "喜欢"]


def test_resolve_words_requires_a_source():
    with pytest.raises(SystemExit):
        cli.resolve_words(_args(argv=[]))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_fields.py -v`
Expected: FAIL — `No module named 'addchin.cli'`.

- [ ] **Step 3: Implement parser, resolution, and field building**

```python
# src/addchin/cli.py
"""Command-line interface for addchin."""

import argparse
from pathlib import Path

from . import anki, cache, chinese, config, doctor, llm


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="addchin",
        description="Build Anki Mandarin cards from words, a file, or a bundled list.",
    )
    p.add_argument("words", nargs="*", help="simplified Chinese words")
    p.add_argument("--file", help="text file with one simplified word per line")
    p.add_argument("--list", dest="list_name", help="bundled list name (see --lists)")
    p.add_argument("--lists", action="store_true", help="show bundled lists and exit")
    p.add_argument("--check", action="store_true", help="check prerequisites and exit")
    p.add_argument("--build-cache", action="store_true", help="maintainer: regenerate cards.json for --list")
    p.add_argument("--deck", default=config.DEFAULT_DECK)
    p.add_argument("--note-type", dest="note_type", default=config.DEFAULT_NOTE_TYPE)
    p.add_argument("--llm-model", dest="llm_model", default=None)
    p.add_argument("--voice", default=config.DEFAULT_VOICE)
    p.add_argument("--no-audio", dest="no_audio", action="store_true")
    p.add_argument("--regenerate", action="store_true", help="force the LLM even on a cache hit")
    p.add_argument("--tags", nargs="*", default=config.DEFAULT_TAGS)
    p.add_argument("--dry-run", dest="dry_run", action="store_true")
    return p


def resolve_words(args) -> list:
    sources = [bool(args.words), bool(args.file), bool(args.list_name)]
    if sum(sources) != 1:
        build_parser().error("provide exactly one of: words, --file, or --list")
    if args.list_name:
        return cache.read_list(args.list_name)
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
        return [w.strip() for w in text.splitlines() if w.strip()]
    return list(args.words)


def card_text_fields(word: str, args) -> dict:
    data = None if args.regenerate else cache.lookup(word)
    if data is None:
        data = llm.generate(word, args.llm_model)
    sentence = data.get("sentence", "")
    return {
        "Simplified": word,
        "Traditional": chinese.to_traditional(word),
        "Pinyin": chinese.to_pinyin(word),
        "Meaning": data.get("meaning", ""),
        "PartOfSpeech": data.get("pos", ""),
        "Audio": "",
        "SentenceSimplified": sentence,
        "SentenceTraditional": chinese.to_traditional(sentence) if sentence else "",
        "SentencePinyin": chinese.to_pinyin(sentence) if sentence else "",
        "SentenceMeaning": data.get("sentence_meaning", ""),
        "SentenceAudio": "",
        "Notes": "",
    }
```

(Note: `main` is added in Task 10; the console script will not run until then.)

- [ ] **Step 4: Run the test**

Run: `uv run pytest tests/test_cli_fields.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/addchin/cli.py tests/test_cli_fields.py
git commit -m "feat: add CLI parser, word resolution, and field building"
```

---

### Task 10: CLI orchestration, audio attach, build-cache, and entry point

**Files:**
- Modify: `src/addchin/cli.py`
- Create: `src/addchin/__main__.py`
- Test: `tests/test_cli_main.py`

**Interfaces:**
- Consumes: everything from Tasks 1–9.
- Produces: `cli.attach_audio(fields: dict, word: str, voice: str)`, `cli.add_card(args, fields) -> str` (returns one of `"added"`, `"skipped"`, `"failed:<msg>"`), `cli.build_cache(args)`, `cli.main(argv=None) -> int`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli_main.py
from addchin import cli


def _args(argv):
    return cli.build_parser().parse_args(argv)


def test_attach_audio_sets_sound_tags(monkeypatch):
    stored = []
    monkeypatch.setattr(cli.chinese, "make_audio", lambda text, voice: b"AUDIO")
    monkeypatch.setattr(cli.anki, "store_media", lambda filename, data: stored.append(filename))
    fields = {"Audio": "", "SentenceAudio": "", "SentenceSimplified": "我有朋友。"}
    cli.attach_audio(fields, "朋友", "zh-CN-XiaoxiaoNeural")
    assert fields["Audio"].startswith("[sound:") and fields["Audio"].endswith(".mp3]")
    assert fields["SentenceAudio"].startswith("[sound:")
    assert len(stored) == 2


def test_add_card_counts_duplicate_as_skipped(monkeypatch):
    def _dup(*a, **k):
        raise cli.anki.AnkiError("cannot create note because it is a duplicate")

    monkeypatch.setattr(cli.anki, "add_note", _dup)
    result = cli.add_card(_args(["朋友", "--no-audio"]), {"Simplified": "朋友"})
    assert result == "skipped"


def test_main_dry_run(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.cache, "lookup",
        lambda w: {"meaning": "friend", "pos": "noun", "sentence": "", "sentence_meaning": ""},
    )
    code = cli.main(["朋友", "--dry-run"])
    assert code == 0
    assert "friend" in capsys.readouterr().out


def test_main_lists(monkeypatch, capsys):
    monkeypatch.setattr(cli.cache, "available_lists", lambda: ["hsk1"])
    assert cli.main(["--lists"]) == 0
    assert "hsk1" in capsys.readouterr().out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_main.py -v`
Expected: FAIL — `module 'addchin.cli' has no attribute 'attach_audio'`.

- [ ] **Step 3: Add orchestration, audio, build-cache, and `main`**

Append to `src/addchin/cli.py`:

```python
import hashlib
import json


def attach_audio(fields: dict, word: str, voice: str) -> None:
    def _store(text: str) -> str:
        name = "addchin_" + hashlib.md5(text.encode("utf-8")).hexdigest()[:12] + ".mp3"
        anki.store_media(name, chinese.make_audio(text, voice))
        return f"[sound:{name}]"

    fields["Audio"] = _store(word)
    sentence = fields.get("SentenceSimplified", "")
    if sentence:
        fields["SentenceAudio"] = _store(sentence)


def add_card(args, fields: dict) -> str:
    try:
        anki.add_note(args.deck, args.note_type, fields, args.tags)
        return "added"
    except anki.AnkiError as exc:
        if "duplicate" in str(exc).lower():
            return "skipped"
        return f"failed:{exc}"


def build_cache(args) -> int:
    if not args.list_name:
        build_parser().error("--build-cache requires --list NAME")
    path = cache.cache_path()
    store = json.loads(path.read_text(encoding="utf-8"))
    words = cache.read_list(args.list_name)
    for i, word in enumerate(words, 1):
        print(f"[{i}/{len(words)}] {word}", flush=True)
        store[word] = llm.generate(word, args.llm_model)
    path.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(store)} entries to {path}")
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.check:
        return 0 if doctor.check() else 1
    if args.lists:
        for name in cache.available_lists():
            print(name)
        return 0
    if args.build_cache:
        return build_cache(args)

    words = resolve_words(args)
    print(f"Loaded {len(words)} word(s).\n")

    if not args.dry_run:
        anki.ensure_deck(args.deck)
        anki.ensure_note_type(args.note_type)

    added = skipped = failed = 0
    for i, word in enumerate(words, 1):
        print(f"[{i}/{len(words)}] {word} ...", flush=True)
        try:
            fields = card_text_fields(word, args)
        except Exception as exc:  # LLM/network failure for one word
            print(f"    FAILED: {exc}")
            failed += 1
            continue

        if args.dry_run:
            for key, value in fields.items():
                print(f"    {key:20} {value}")
            added += 1
            continue

        if not args.no_audio:
            attach_audio(fields, word, args.voice)

        result = add_card(args, fields)
        if result == "added":
            print(f"    added: {fields['Pinyin']} — {fields['Meaning']}")
            added += 1
        elif result == "skipped":
            print("    skipped (already in deck)")
            skipped += 1
        else:
            print(f"    {result.replace('failed:', 'FAILED: ')}")
            failed += 1

    print(f"\nDone. added={added} skipped={skipped} failed={failed}")
    if not args.dry_run and added:
        print("Tip: in Anki, run Tools > Check Media if audio doesn't play.")
    return 0
```

```python
# src/addchin/__main__.py
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -v`
Expected: PASS (all tests across all tasks).

- [ ] **Step 5: Commit**

```bash
git add src/addchin/cli.py src/addchin/__main__.py tests/test_cli_main.py
git commit -m "feat: add CLI orchestration, audio, build-cache, and entry point"
```

---

### Task 11: One-line installer

**Files:**
- Create: `install.sh` (overwrites the current one)
- Test: manual (shell script; no pytest)

**Interfaces:**
- Consumes: the published repo.
- Produces: an `install.sh` runnable via `curl -fsSL <raw-url> | bash`.

- [ ] **Step 1: Write the installer**

```bash
#!/usr/bin/env bash
# Install addchin. Run directly:
#   curl -fsSL https://raw.githubusercontent.com/bartaat/addchin/main/install.sh | bash
set -euo pipefail

REPO="https://github.com/bartaat/addchin"

have() { command -v "$1" >/dev/null 2>&1; }

if ! have uv; then
  echo "Installing uv (https://docs.astral.sh/uv/)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # uv installs to ~/.local/bin or ~/.cargo/bin; make it visible for this run
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if have uv; then
  echo "Installing addchin with uv..."
  uv tool install --from "git+$REPO" addchin
  echo
  echo "Installed. Ensure your uv tools dir is on PATH (uv tool update-shell), then run:"
  echo "    addchin --check"
  exit 0
fi

echo "uv unavailable; falling back to a pip virtual environment."
BIN_DIR="$HOME/.local/bin"
VENV_DIR="$HOME/.local/share/addchin-venv"
mkdir -p "$BIN_DIR"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
"$VENV_DIR/bin/pip" install "git+$REPO"
ln -sf "$VENV_DIR/bin/addchin" "$BIN_DIR/addchin"
echo
echo "Installed: $BIN_DIR/addchin"
case ":$PATH:" in
  *":$BIN_DIR:"*) echo "Run: addchin --check" ;;
  *) echo "Add ~/.local/bin to your PATH, then run: addchin --check" ;;
esac
```

- [ ] **Step 2: Lint the script**

Run: `bash -n install.sh && (have_sc=$(command -v shellcheck) && shellcheck install.sh || echo "shellcheck not installed; skipped")`
Expected: no syntax errors (shellcheck optional).

- [ ] **Step 3: Make it executable and commit**

```bash
chmod +x install.sh
git add install.sh
git commit -m "feat: replace installer with one-line uv-based install.sh"
```

---

### Task 12: README, LICENSE, and remove the legacy script

**Files:**
- Modify: `README.md` (replace the placeholder from Task 1)
- Create: `LICENSE`
- Delete: `generate_cards.py`, `words.txt` (superseded by the package)

**Interfaces:**
- Consumes: the finished CLI.
- Produces: discoverable docs.

- [ ] **Step 1: Write the README**

```markdown
# addchin

**Turn a list of Chinese words into fully-formed Anki flashcards — in one command.**

addchin writes the meaning and a natural example sentence with Claude, then adds
traditional characters, pinyin, and native-quality audio locally, and inserts the
finished card into Anki. It auto-creates the deck and note type, so there is
nothing to configure.

## 30-second quickstart

```bash
curl -fsSL https://raw.githubusercontent.com/bartaat/addchin/main/install.sh | bash
addchin --check          # verify Anki + AnkiConnect
addchin --list hsk1      # build a starter deck (free — no credits used)
```

## What you get

Each card has: simplified + traditional, pinyin, meaning, part of speech, word
audio, and an example sentence with its pinyin, translation, and audio.

## Prerequisites

- [Anki](https://apps.ankiweb.net/) with the **AnkiConnect** add-on (code `2055492159`), open while addchin runs.
- For words **not** in the bundled cache: an `ANTHROPIC_API_KEY`, **or** the [Claude CLI](https://claude.com/claude-code). Bundled lists need neither.

## Usage

```bash
addchin 朋友 图书馆        # inline words
addchin --file words.txt   # one word per line
addchin --list hsk1        # a bundled list
addchin --lists            # show bundled lists
addchin --dry-run 朋友     # preview without adding
```

## How it saves credits

Bundled lists ship with their language fields pre-generated, so building them
makes **zero** Claude calls — only the free local steps (pinyin, traditional,
audio) run. Claude is called only for words not already in the cache, or when you
pass `--regenerate`.

## Configuration

| Flag | Default | Purpose |
|---|---|---|
| `--deck` | `Addchin Mandarin` | Target deck (auto-created) |
| `--note-type` | `Addchin Mandarin` | Note type (auto-created) |
| `--llm-model` | `claude-opus-4-8` | Model for cache misses (e.g. `claude-haiku-4-5` for cheap bulk) |
| `--voice` | `zh-CN-XiaoxiaoNeural` | edge-tts voice |
| `--no-audio` | off | Skip audio |
| `--regenerate` | off | Force the LLM even on a cache hit |
| `--tags` | `addchin` | Tags for new notes |

## Troubleshooting

- **"Could not reach AnkiConnect"** — open Anki and install AnkiConnect (code `2055492159`).
- **Audio not playing** — in Anki, run **Tools ▸ Check Media**.

## License & credits

MIT. Card content is generated with [Claude](https://claude.com); audio uses
Microsoft Edge neural voices via [edge-tts](https://github.com/rany2/edge-tts);
notes are added through [AnkiConnect](https://foosoft.net/projects/anki-connect/).
Inspired by the Refold Mandarin approach to vocabulary cards.
```

- [ ] **Step 2: Write the LICENSE**

```text
MIT License

Copyright (c) 2026 addchin contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Remove the legacy single-file script**

```bash
git rm generate_cards.py words.txt
```

- [ ] **Step 4: Verify the package still builds and tests pass**

Run: `uv run pytest -v && uv build`
Expected: tests PASS; `uv build` produces a wheel and sdist in `dist/`.

- [ ] **Step 5: Commit**

```bash
git add README.md LICENSE
git commit -m "docs: add README and LICENSE; remove legacy script"
```

---

## Self-Review

**Spec coverage:**
- Package layout → Tasks 1–10 create every module in the spec.
- Dual LLM backend with structured outputs → Task 7.
- Auto-create deck + self-contained note type → Tasks 5 & 6.
- Content cache + maintainer `build-cache` + bundled lists → Tasks 4 & 10.
- CLI surface (inline/file/list/lists/check/dry-run/flags) → Tasks 9 & 10.
- One-line installer → Task 11.
- README + discoverability + LICENSE → Task 12.
- Testing strategy (pure modules, mocked network) → Tasks 2–10.
- Error handling (friendly AnkiConnect error, duplicate=skip, per-word failures) → Tasks 6, 10.
- Migration (split file, rename defaults, rewrite installer, remove legacy) → Tasks 1–12.

**Placeholder scan:** No TBD/TODO; every code step shows complete code. The one
in-place correction (audio call argument) is shown with the exact replacement
line in Task 10 Step 3.

**Type consistency:** `card_text_fields` produces the 12 fields used by
`attach_audio`/`add_card`; `llm.generate(word, model)` signature matches all call
sites; `anki.add_note(deck, note_type, fields, tags)` matches `add_card`;
`cache.lookup/read_list/available_lists/cache_path` match all CLI uses.
