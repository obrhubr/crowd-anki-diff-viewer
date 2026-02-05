"""Parser for crowd-anki deck JSON files."""

import json
from pathlib import Path
from typing import Dict, Tuple, Optional
from .models import Deck, Note, NoteModel, FieldModel, Template


def parse_deck(json_path: str) -> Tuple[Deck, Dict[str, NoteModel]]:
    """
    Parse a crowd-anki deck.json file.

    Args:
        json_path: Path to the deck.json file

    Returns:
        Tuple of (root_deck, note_models_dict)
        where note_models_dict maps crowdanki_uuid to NoteModel

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
        ValueError: If the deck structure is invalid
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Deck file not found: {json_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract note models first (at root level)
    note_models = {}
    if 'note_models' in data:
        for nm_data in data['note_models']:
            try:
                # Parse fields
                fields = [FieldModel(**field) for field in nm_data.get('flds', [])]

                # Parse templates
                templates = [Template(**tmpl) for tmpl in nm_data.get('tmpls', [])]

                # Create note model
                note_model = NoteModel(
                    crowdanki_uuid=nm_data['crowdanki_uuid'],
                    name=nm_data['name'],
                    type=nm_data['type'],
                    flds=fields,
                    tmpls=templates,
                    css=nm_data.get('css', ''),
                    latexPre=nm_data.get('latexPre', ''),
                    latexPost=nm_data.get('latexPost', ''),
                    latexsvg=nm_data.get('latexsvg', False),
                    req=nm_data.get('req', []),
                    sortf=nm_data.get('sortf', 0),
                    did=nm_data.get('did'),
                    mod=nm_data.get('mod', 0),
                    tags=nm_data.get('tags', []),
                    usn=nm_data.get('usn', -1),
                    vers=nm_data.get('vers', []),
                    originalId=nm_data.get('originalId'),
                    originalStockKind=nm_data.get('originalStockKind')
                )
                note_models[nm_data['crowdanki_uuid']] = note_model
            except Exception as e:
                raise ValueError(f"Failed to parse note model '{nm_data.get('name', 'unknown')}': {e}")

    # Parse deck hierarchy recursively
    root_deck = _parse_deck_recursive(data, parent_path="")

    return root_deck, note_models


def parse_deck_from_string(json_string: str) -> Tuple[Deck, Dict[str, NoteModel]]:
    """
    Parse a crowd-anki deck from a JSON string.

    Args:
        json_string: JSON string content

    Returns:
        Tuple of (root_deck, note_models_dict)
    """
    data = json.loads(json_string)

    # Extract note models
    note_models = {}
    if 'note_models' in data:
        for nm_data in data['note_models']:
            fields = [FieldModel(**field) for field in nm_data.get('flds', [])]
            templates = [Template(**tmpl) for tmpl in nm_data.get('tmpls', [])]

            note_model = NoteModel(
                crowdanki_uuid=nm_data['crowdanki_uuid'],
                name=nm_data['name'],
                type=nm_data['type'],
                flds=fields,
                tmpls=templates,
                css=nm_data.get('css', ''),
                latexPre=nm_data.get('latexPre', ''),
                latexPost=nm_data.get('latexPost', ''),
                latexsvg=nm_data.get('latexsvg', False),
                req=nm_data.get('req', []),
                sortf=nm_data.get('sortf', 0),
                did=nm_data.get('did'),
                mod=nm_data.get('mod', 0),
                tags=nm_data.get('tags', []),
                usn=nm_data.get('usn', -1),
                vers=nm_data.get('vers', []),
                originalId=nm_data.get('originalId'),
                originalStockKind=nm_data.get('originalStockKind')
            )
            note_models[nm_data['crowdanki_uuid']] = note_model

    root_deck = _parse_deck_recursive(data, parent_path="")

    return root_deck, note_models


def _parse_deck_recursive(deck_data: dict, parent_path: str) -> Deck:
    """
    Recursively parse nested deck structure.

    Args:
        deck_data: Dictionary containing deck data
        parent_path: Path to parent deck (e.g., "Root::Child")

    Returns:
        Parsed Deck object
    """
    # Build deck path
    deck_name = deck_data['name']
    deck_path = f"{parent_path}::{deck_name}" if parent_path else deck_name

    # Parse notes
    notes = []
    for note_data in deck_data.get('notes', []):
        try:
            note = Note(
                guid=note_data['guid'],
                note_model_uuid=note_data['note_model_uuid'],
                fields=note_data['fields'],
                tags=note_data.get('tags', [])
            )
            notes.append(note)
        except Exception as e:
            # Log error but continue parsing other notes
            print(f"Warning: Failed to parse note {note_data.get('guid', 'unknown')}: {e}")

    # Create deck object
    deck = Deck(
        name=deck_name,
        crowdanki_uuid=deck_data['crowdanki_uuid'],
        notes=notes,
        media_files=deck_data.get('media_files', []),
        deck_config_uuid=deck_data.get('deck_config_uuid'),
        desc=deck_data.get('desc', ''),
        dyn=deck_data.get('dyn', 0),
        extendNew=deck_data.get('extendNew', 0),
        extendRev=deck_data.get('extendRev', 0),
        newLimit=deck_data.get('newLimit'),
        newLimitToday=deck_data.get('newLimitToday'),
        reviewLimit=deck_data.get('reviewLimit'),
        reviewLimitToday=deck_data.get('reviewLimitToday'),
        desiredRetention=deck_data.get('desiredRetention'),
        mid=deck_data.get('mid')
    )

    # Recursively parse children
    for child_data in deck_data.get('children', []):
        child_deck = _parse_deck_recursive(child_data, deck_path)
        deck.children.append(child_deck)

    return deck


def find_note_by_guid(deck: Deck, guid: str, current_path: str = "") -> Optional[Tuple[Note, str]]:
    """
    Find a note by its GUID in the deck hierarchy.

    Args:
        deck: Root deck to search
        guid: GUID to search for
        current_path: Current deck path (used for recursion)

    Returns:
        Tuple of (Note, deck_path) if found, None otherwise
    """
    deck_path = f"{current_path}::{deck.name}" if current_path else deck.name

    # Search in current deck
    for note in deck.notes:
        if note.guid == guid:
            return (note, deck_path)

    # Search in children
    for child in deck.children:
        result = find_note_by_guid(child, guid, deck_path)
        if result:
            return result

    return None


def build_note_map(deck: Deck, current_path: str = "") -> Dict[str, Tuple[Note, str]]:
    """
    Build a dictionary mapping GUIDs to (Note, deck_path) tuples.

    Args:
        deck: Root deck
        current_path: Current deck path (used for recursion)

    Returns:
        Dictionary mapping GUID to (Note, deck_path)
    """
    deck_path = f"{current_path}::{deck.name}" if current_path else deck.name
    note_map = {}

    # Add notes from current deck
    for note in deck.notes:
        note_map[note.guid] = (note, deck_path)

    # Recursively add notes from children
    for child in deck.children:
        note_map.update(build_note_map(child, deck_path))

    return note_map


def validate_deck_structure(deck: Deck, note_models: Dict[str, NoteModel]) -> bool:
    """
    Validate that all notes reference valid note models.

    Args:
        deck: Deck to validate
        note_models: Dictionary of available note models

    Returns:
        True if valid, False otherwise
    """
    def _validate_recursive(d: Deck) -> bool:
        # Check all notes
        for note in d.notes:
            if note.note_model_uuid not in note_models:
                print(f"Warning: Note {note.guid} references unknown note model {note.note_model_uuid}")
                return False

            # Check field count matches
            note_model = note_models[note.note_model_uuid]
            if len(note.fields) != len(note_model.flds):
                print(f"Warning: Note {note.guid} has {len(note.fields)} fields but model expects {len(note_model.flds)}")
                return False

        # Recursively validate children
        for child in d.children:
            if not _validate_recursive(child):
                return False

        return True

    return _validate_recursive(deck)
