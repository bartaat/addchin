# addchin — Public Release Design

**Date:** 2026-06-18
**Status:** Approved (design); pending implementation plan
**Repo:** https://github.com/bartaat/addchin

## Summary

`addchin` turns a list of simplified-Chinese words into fully-formed Anki
flashcards. For each word, Claude supplies the *language* fields (meaning, part
of speech, an example sentence and its translation) while local libraries supply
the *mechanical* fields (traditional characters via OpenCC, pinyin via pypinyin,
audio via edge-tts). AnkiConnect inserts the finished note.

This design takes the current single-file, setup-heavy script and turns it into a
discoverable public project that is **easy to install** (one-line installer) and
**does as much work on its own as possible** (auto-creates the Anki deck and note
type, ships pre-generated content so starter decks cost zero credits, and accepts
words inline / from a file / from bundled lists).

## Goals

- Install with a single command; no manual venv, no manual Anki note-type import.
- A first run produces a working deck with no hand-configuration of Anki.
- Building a bundled starter deck costs the user **$0** (no LLM calls) — only the
  free local steps run.
- Calling Claude is the *optional* path, used for cache misses or `--regenerate`.
- A clear, attractive README that makes the project discoverable.
- Clean module boundaries so the project is contributor-friendly and testable.

## Non-goals

- Redistributing the official Refold Mandarin 1k vocabulary list (licensing risk).
- Supporting languages other than Mandarin.
- A GUI. addchin is a CLI.
- Publishing to PyPI in this iteration (the curl installer covers distribution;
  PyPI can come later).

## Key decisions

| Decision | Choice | Rationale |
|---|---|---|
| LLM backend | Auto-detect `ANTHROPIC_API_KEY` (official `anthropic` SDK); fall back to the `claude` CLI | Works for newcomers with an API key *and* existing Claude Code users |
| Anki setup | Auto-create deck **and** a self-contained note type via AnkiConnect | Removes the biggest hidden prerequisite |
| Install | One-line `curl … | bash` using `uv` (fallback pip/venv) | No PyPI account needed; works straight from the repo |
| Bundled content | Ship pre-generated language fields as `cards.json`; LLM is opt-in | Starter decks cost no credits; generation is the exception, not the rule |
| Code shape | Small Python package with focused modules | Maintainable, testable, contributor-friendly |
| Default model | `claude-opus-4-8`, overridable via `--llm-model` | Follows Anthropic default; users can pick `claude-haiku-4-5` for cheap bulk |

## Architecture

### Package layout

```
addchin/
├── pyproject.toml          # metadata, deps, `addchin` console entry point
├── README.md
├── LICENSE                 # MIT
├── install.sh              # one-line curl installer (uv, falls back to pip/venv)
├── src/addchin/
│   ├── __init__.py
│   ├── __main__.py         # python -m addchin
│   ├── cli.py              # argparse + orchestration loop
│   ├── config.py           # defaults (deck, note type, voice, model)
│   ├── llm.py              # language fields: cache → API → claude CLI
│   ├── cache.py            # load bundled content cache; lookup/merge
│   ├── chinese.py          # to_traditional / to_pinyin / make_audio
│   ├── anki.py             # AnkiConnect: ensure_deck, ensure_note_type, add_note, store_media
│   ├── templates.py        # note type fields + card HTML/CSS
│   ├── doctor.py           # `addchin --check` prerequisite checks
│   └── data/
│       ├── lists/          # hsk1.txt, … (plain word lists, one word per line)
│       └── cache/cards.json  # pre-generated language fields (committed)
└── tests/                  # pytest
```

### Module responsibilities

- **`config.py`** — Defaults and constants: AnkiConnect URL (`http://localhost:8765`),
  default deck name, default note type (`Addchin Mandarin`), default voice
  (`zh-CN-XiaoxiaoNeural`), default LLM model (`claude-opus-4-8`). No logic.
- **`chinese.py`** — Pure, local, no network beyond edge-tts:
  - `to_traditional(text) -> str` (OpenCC `s2t`)
  - `to_pinyin(text) -> str` (pypinyin, tone marks, space-separated)
  - `make_audio(text, voice) -> bytes` (edge-tts) — returns mp3 bytes; storing in
    Anki is `anki.py`'s job.
- **`cache.py`** — Loads `data/cache/cards.json` (a map
  `word -> {meaning, pos, sentence, sentence_meaning}`). `lookup(word)` returns the
  dict or `None`.
- **`llm.py`** — `generate(word, model) -> {meaning, pos, sentence, sentence_meaning}`.
  Backend resolution:
  1. If `ANTHROPIC_API_KEY` is set → official `anthropic` SDK,
     `client.messages.create(...)` with `output_config={"format": {"type":
     "json_schema", "schema": ...}}` so the response is guaranteed valid JSON.
     Default `model="claude-opus-4-8"`.
  2. Else if `claude` is on PATH → `claude -p <prompt>` and parse JSON (keep the
     defensive code-fence stripping for this path).
  3. Else → raise a clear error telling the user to set `ANTHROPIC_API_KEY` or
     install the Claude CLI.
  The orchestration layer (`cli.py`) tries `cache.lookup` first and only calls
  `llm.generate` on a miss or when `--regenerate` is set.
- **`anki.py`** — AnkiConnect client. `invoke(action, **params)`, `ensure_deck(name)`
  (`createDeck`), `ensure_note_type(name)` (checks `modelNames`, calls `createModel`
  with fields + templates from `templates.py` if missing), `store_media(filename, bytes)`
  (`storeMediaFile`), `add_note(...)`. Raises a typed error if AnkiConnect is
  unreachable so `cli.py` can print friendly guidance.
- **`templates.py`** — The note-type definition: field list, card front/back HTML,
  and CSS. Single source of truth for `createModel`.
- **`doctor.py`** — `check()` verifies: Anki running + AnkiConnect reachable,
  an LLM backend available (API key or `claude` CLI), and required Python deps
  importable. Prints a checklist with fix instructions; used by `--check`.
- **`cli.py`** — Argument parsing and the per-word loop (load words → build fields
  → add note), with the added/skipped/failed tally and friendly error handling.

### Data flow (one word)

```
word
 └─ cache.lookup(word) ──hit──▶ language fields ($0)
        │miss / --regenerate
        ▼
     llm.generate(word)  (API key → anthropic SDK, else claude CLI)
 then (always, free, local):
   chinese.to_traditional / to_pinyin / make_audio
 then:
   anki.store_media + anki.add_note  (deck & note type auto-created if missing)
```

## The content cache (credit-saving mechanism)

Generating language fields with Claude costs money; the local steps (pinyin,
traditional, edge-tts audio) are free. To make bundled starter decks free:

- `data/cache/cards.json` ships **pre-generated** language fields for the words in
  the bundled lists, committed to the repo.
- A maintainer-only command, `addchin build-cache --list <name>`, runs the LLM over
  a word list and writes/updates `cards.json`. Maintainers run it once and commit
  the result.
- End users running `addchin --list hsk1` get a full deck from the cache with **no
  LLM calls** — only the free local steps execute.
- Users supplying their own words hit the cache first; cache misses call the LLM.
  `--regenerate` forces a fresh LLM call even on a hit.

Audio is **not** cached (edge-tts is free and fast; caching mp3s would bloat the
repo). `cards.json` stays small (text only).

## Anki auto-creation + card design

On every run, `anki.py` ensures the deck and note type exist:

- `ensure_deck(deck)` → `createDeck`.
- `ensure_note_type(note_type)` → if not in `modelNames`, `createModel` using
  `templates.py`.

Self-contained note type **"Addchin Mandarin"**, fields:

```
Simplified, Traditional, Pinyin, Meaning, PartOfSpeech, Audio,
SentenceSimplified, SentenceTraditional, SentencePinyin, SentenceMeaning,
SentenceAudio, Notes
```

Card:

- **Front:** large simplified word + auto-playing word audio.
- **Back:** pinyin · part of speech · meaning · traditional, then the example
  sentence (simplified) with its pinyin, English translation, and sentence audio.
- Clean, readable CSS with no external assets.

Users who prefer the official Refold deck can point addchin at it with
`--note-type "Refold Mandarin 1k"` (auto-creation is skipped when the note type
already exists).

## CLI surface

```
addchin 朋友 图书馆          # inline words
addchin --file words.txt      # from a file (one word per line)
addchin --list hsk1           # bundled list (free, from the cache)
addchin --lists               # list bundled word lists
addchin --check               # doctor: verify Anki, AnkiConnect, backend, deps
addchin --dry-run             # build & print fields, don't add to Anki

Flags:
  --deck NAME            (default: Addchin Mandarin)
  --note-type NAME       (default: Addchin Mandarin)
  --llm-model ID         (default: claude-opus-4-8)
  --voice VOICE          (default: zh-CN-XiaoxiaoNeural)
  --no-audio             skip TTS
  --regenerate           force LLM even on a cache hit
  --tags TAG...          (default: addchin)

Maintainer:
  addchin build-cache --list NAME    regenerate cards.json (costs credits)
```

Exactly one word source per run (inline args, `--file`, or `--list`). Errors are
friendly: an unreachable AnkiConnect prints the exact fix, not a stack trace.

## Install script

`curl -fsSL https://raw.githubusercontent.com/bartaat/addchin/main/install.sh | bash`

Behaviour:

1. If `uv` is present → `uv tool install` from the repo (isolated, on PATH).
2. Else if `uv` can be installed → install `uv`, then as above.
3. Else → create a pip venv, install the package, and symlink an `addchin` wrapper
   into `~/.local/bin`.
4. Print whether `~/.local/bin` is on PATH and the single next command to run.

Replaces today's venv-coupled `install.sh`.

## README

Sections, in order:

1. Title + one-line hook.
2. 30-second quickstart (install one-liner → first deck).
3. "What you get" — a card description/screenshot.
4. Prerequisites — Anki + AnkiConnect (add-on code `2055492159`); optionally an
   Anthropic API key *or* the Claude CLI.
5. Install (the one-liner).
6. Usage examples (inline / file / list).
7. How the cache saves credits.
8. Configuration table (flags).
9. Troubleshooting (AnkiConnect not running, audio not playing → Tools ▸ Check Media).
10. License + credits (MIT; nod to Refold and AnkiConnect).

GitHub topics for discoverability: `anki`, `mandarin`, `chinese`,
`spaced-repetition`, `flashcards`, `language-learning`, `claude`, `edge-tts`.

## Dependencies

Runtime: `anthropic`, `requests`, `pypinyin`, `opencc-python-reimplemented`,
`edge-tts`. Dev: `pytest`. Declared in `pyproject.toml`; Python 3.9+.

## Testing

`pytest` over the pure modules — no live network:

- `chinese.py` — pinyin and traditional conversion on known inputs.
- `cache.py` — lookup hit/miss and field merge.
- `templates.py` — note-type schema shape (fields present, templates non-empty).
- `cli.py` — argument parsing and the per-word loop with `anki.py` and `llm.py`
  mocked; verifies cache-first behaviour and `--regenerate`.

## Error handling

- AnkiConnect unreachable → typed error → `cli.py` prints how to start Anki / install
  the add-on.
- No LLM backend on a cache miss → clear message naming both options
  (`ANTHROPIC_API_KEY` or the Claude CLI).
- Duplicate note → counted as "skipped", not a failure (AnkiConnect duplicate scope).
- Per-word failures are caught, counted, and reported in the final tally; one bad
  word does not abort the run.

## Migration from the current code

- `generate_cards.py` → split into the modules above.
- The hard-coded `Refold Mandarin 1k` note type and `decky deck 1` deck become the
  auto-created `Addchin Mandarin` defaults (still overridable).
- `claude_lang_data` (CLI-only) → `llm.generate` with the API path added and
  structured outputs on the API path.
- `install.sh` rewritten to the uv-based one-liner.
