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
    assert fields["AudioFile"] == ""
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
