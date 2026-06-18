"""AnkiConnect client: deck/note-type creation, media, and notes."""

import base64

import requests

from . import config, templates


class AnkiError(RuntimeError):
    pass


def invoke(action: str, **params):
    body = {"action": action, "version": 6, "params": params}
    try:
        resp = requests.post(config.ANKI_URL, json=body, timeout=30)
    except requests.exceptions.RequestException as exc:
        raise AnkiError(
            f"Could not reach AnkiConnect at {config.ANKI_URL}. "
            f"Open Anki and install the AnkiConnect add-on (code {config.ANKI_ADDON_CODE})."
        ) from exc
    payload = resp.json()
    if payload.get("error") is not None:
        raise AnkiError(f"AnkiConnect error on {action}: {payload['error']}")
    return payload["result"]


def ensure_deck(deck: str) -> None:
    invoke("createDeck", deck=deck)


def ensure_note_type(note_type: str) -> None:
    if note_type not in invoke("modelNames"):
        invoke("createModel", **templates.model_spec(note_type))
        return
    # Already exists — keep it in sync so template/field/styling changes from a
    # newer addchin version reach decks created by an older one.
    existing = invoke("modelFieldNames", modelName=note_type)
    for field in templates.NOTE_TYPE_FIELDS:
        if field not in existing:
            invoke("modelFieldAdd", modelName=note_type, fieldName=field, index=len(existing))
            existing.append(field)
    invoke(
        "updateModelTemplates",
        model={"name": note_type, "templates": {templates.CARD_NAME: {"Front": templates.FRONT, "Back": templates.BACK}}},
    )
    invoke("updateModelStyling", model={"name": note_type, "css": templates.CSS})


def store_media(filename: str, data: bytes) -> None:
    invoke("storeMediaFile", filename=filename, data=base64.b64encode(data).decode("ascii"))


def add_note(deck: str, note_type: str, fields: dict, tags: list) -> int:
    note = {
        "deckName": deck,
        "modelName": note_type,
        "fields": fields,
        "tags": tags,
        "options": {"allowDuplicate": False, "duplicateScope": "deck"},
    }
    return invoke("addNote", note=note)
