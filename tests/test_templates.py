from addchin import templates


def test_fields_present():
    for field in ("Simplified", "Pinyin", "Meaning", "AudioFile", "SentenceSimplified", "Notes"):
        assert field in templates.NOTE_TYPE_FIELDS


def test_model_spec_shape():
    spec = templates.model_spec("Addchin Mandarin")
    assert spec["modelName"] == "Addchin Mandarin"
    assert spec["inOrderFields"] == templates.NOTE_TYPE_FIELDS
    assert spec["css"].strip() != ""
    card = spec["cardTemplates"][0]
    assert "{{Simplified}}" in card["Front"]
    assert "{{Meaning}}" in card["Back"]


def test_front_audio_does_not_autoplay():
    front = templates.model_spec("Addchin Mandarin")["cardTemplates"][0]["Front"]
    # Manual <audio controls> player, never an auto-playing [sound:] tag.
    assert "<audio controls" in front
    assert "autoplay" not in front
    assert "{{Audio}}" not in front
