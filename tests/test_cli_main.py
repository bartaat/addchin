# tests/test_cli_main.py
from addchin import cli


def _args(argv):
    return cli.build_parser().parse_args(argv)


def test_attach_audio_word_manual_sentence_autoplay(monkeypatch):
    stored = []
    monkeypatch.setattr(cli.chinese, "make_audio", lambda text, voice: b"AUDIO")
    monkeypatch.setattr(cli.anki, "store_media", lambda filename, data: stored.append(filename))
    fields = {"AudioFile": "", "SentenceAudio": "", "SentenceSimplified": "我有朋友。"}
    cli.attach_audio(fields, "朋友", "zh-CN-XiaoxiaoNeural")
    # Word audio is a bare filename (manual <audio> player), NOT a [sound:] tag.
    assert fields["AudioFile"].endswith(".mp3")
    assert not fields["AudioFile"].startswith("[sound:")
    # Sentence audio keeps the [sound:] tag so it auto-plays on the back.
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
