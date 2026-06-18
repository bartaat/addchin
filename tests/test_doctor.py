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
