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
