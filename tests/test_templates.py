from addchin import templates


def test_fields_present():
    for field in ("Simplified", "Pinyin", "Meaning", "Audio", "SentenceSimplified", "Notes"):
        assert field in templates.NOTE_TYPE_FIELDS


def test_model_spec_shape():
    spec = templates.model_spec("Addchin Mandarin")
    assert spec["modelName"] == "Addchin Mandarin"
    assert spec["inOrderFields"] == templates.NOTE_TYPE_FIELDS
    assert spec["css"].strip() != ""
    card = spec["cardTemplates"][0]
    assert "{{Simplified}}" in card["Front"]
    assert "{{Meaning}}" in card["Back"]
