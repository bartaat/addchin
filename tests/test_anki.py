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


def test_ensure_note_type_syncs_when_present(monkeypatch):
    calls = []

    def fake_invoke(action, **params):
        calls.append((action, params))
        if action == "modelNames":
            return ["Addchin Mandarin"]
        if action == "modelFieldNames":
            return ["Simplified", "Audio"]  # stale: missing AudioFile etc.
        return None

    monkeypatch.setattr(anki, "invoke", fake_invoke)
    anki.ensure_note_type("Addchin Mandarin")
    actions = [c[0] for c in calls]
    assert "createModel" not in actions  # never recreate an existing model
    assert "updateModelTemplates" in actions
    assert "updateModelStyling" in actions
    added = [c[1]["fieldName"] for c in calls if c[0] == "modelFieldAdd"]
    assert "AudioFile" in added  # missing field gets added

    # The pushed front template is the manual player, never the autoplay tag.
    tmpl = next(c[1] for c in calls if c[0] == "updateModelTemplates")
    front = tmpl["model"]["templates"]["Recognition"]["Front"]
    assert "<audio controls" in front and "{{Audio}}" not in front
