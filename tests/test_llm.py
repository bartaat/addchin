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


def test_generate_api_passes_structured_output(monkeypatch):
    captured = {}

    class _CapClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                captured.update(kwargs)
                return _Resp()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(llm.anthropic, "Anthropic", lambda: _CapClient())
    llm.generate("朋友")
    assert captured["model"] == "claude-opus-4-8"
    assert captured["output_config"]["format"]["type"] == "json_schema"
    assert set(captured["output_config"]["format"]["schema"]["required"]) == {
        "meaning", "pos", "sentence", "sentence_meaning",
    }
