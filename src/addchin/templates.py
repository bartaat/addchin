"""The self-contained "Addchin Mandarin" note type."""

NOTE_TYPE_FIELDS = [
    "Simplified",
    "Traditional",
    "Pinyin",
    "Meaning",
    "PartOfSpeech",
    "AudioFile",
    "SentenceSimplified",
    "SentenceTraditional",
    "SentencePinyin",
    "SentenceMeaning",
    "SentenceAudio",
    "Notes",
]

CARD_NAME = "Recognition"

# Word audio is a manual <audio controls> player (no `autoplay`), so the
# pronunciation only plays when clicked — Anki auto-plays `[sound:]` fields, so
# we reference the stored media file directly instead.
FRONT = """<div class="hanzi">{{Simplified}}</div>
{{#AudioFile}}<audio controls src="{{AudioFile}}"></audio>{{/AudioFile}}"""

BACK = """{{FrontSide}}
<hr id="answer">
<div class="pinyin">{{Pinyin}}</div>
<div class="meaning">{{Meaning}} <span class="pos">{{PartOfSpeech}}</span></div>
<div class="traditional">繁體 {{Traditional}}</div>
<div class="sentence">{{SentenceSimplified}}</div>
<div class="sentence-pinyin">{{SentencePinyin}}</div>
<div class="sentence-meaning">{{SentenceMeaning}}</div>
{{SentenceAudio}}
<div class="notes">{{Notes}}</div>"""

CSS = """.card {
  font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
  font-size: 20px;
  text-align: center;
  color: #1a1a1a;
  background: #fbfbfb;
}
.hanzi { font-size: 64px; margin: 24px 0; }
audio { margin-top: 12px; height: 32px; }
.pinyin { font-size: 26px; color: #c0392b; margin-top: 12px; }
.meaning { font-size: 24px; margin: 8px 0; }
.pos { font-size: 16px; color: #888; }
.traditional { font-size: 16px; color: #888; margin-bottom: 16px; }
.sentence { font-size: 24px; margin-top: 16px; }
.sentence-pinyin { font-size: 18px; color: #c0392b; }
.sentence-meaning { font-size: 18px; color: #555; }
.notes { font-size: 14px; color: #999; margin-top: 16px; }
hr#answer { margin: 20px 0; }"""


def model_spec(model_name: str) -> dict:
    """Return an AnkiConnect `createModel` payload for the note type."""
    return {
        "modelName": model_name,
        "inOrderFields": NOTE_TYPE_FIELDS,
        "css": CSS,
        "isCloze": False,
        "cardTemplates": [
            {"Name": CARD_NAME, "Front": FRONT, "Back": BACK}
        ],
    }
