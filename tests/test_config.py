from addchin import config


def test_defaults():
    assert config.ANKI_URL == "http://localhost:8765"
    assert config.ANKI_ADDON_CODE == "2055492159"
    assert config.DEFAULT_DECK == "Addchin Mandarin"
    assert config.DEFAULT_NOTE_TYPE == "Addchin Mandarin"
    assert config.DEFAULT_VOICE == "zh-CN-XiaoxiaoNeural"
    assert config.DEFAULT_LLM_MODEL == "claude-opus-4-8"
    assert config.DEFAULT_TAGS == ["addchin"]
