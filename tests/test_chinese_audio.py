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
