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
