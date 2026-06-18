"""Command-line interface for addchin."""

import argparse
import hashlib
import json
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
        "AudioFile": "",
        "SentenceSimplified": sentence,
        "SentenceTraditional": chinese.to_traditional(sentence) if sentence else "",
        "SentencePinyin": chinese.to_pinyin(sentence) if sentence else "",
        "SentenceMeaning": data.get("sentence_meaning", ""),
        "SentenceAudio": "",
        "Notes": "",
    }


def attach_audio(fields: dict, word: str, voice: str) -> None:
    def _store(text: str) -> str:
        name = "addchin_" + hashlib.md5(text.encode("utf-8")).hexdigest()[:12] + ".mp3"
        anki.store_media(name, chinese.make_audio(text, voice))
        return name

    # Word audio is a bare filename → rendered as a click-to-play <audio> control
    # (no auto-play). Sentence audio uses [sound:] so it auto-plays on the back.
    fields["AudioFile"] = _store(word)
    sentence = fields.get("SentenceSimplified", "")
    if sentence:
        fields["SentenceAudio"] = f"[sound:{_store(sentence)}]"


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
        if word in store and not args.regenerate:
            print(f"[{i}/{len(words)}] {word} (cached, skipping)", flush=True)
            continue
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
