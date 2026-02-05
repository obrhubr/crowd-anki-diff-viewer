"""Git diff detection for crowd-anki decks."""

import git
from pathlib import Path
from typing import List, Dict, Tuple
from .models import Deck, Note, NoteModel, NoteChange
from .parser import parse_deck_from_string, build_note_map
from .change_classifier import classify_note_change, get_change_description


def detect_note_changes(repo_path: str = ".", commit: str = "HEAD") -> List[NoteChange]:
    """
    Detect note changes in the most recent commit.

    Args:
        repo_path: Path to git repository
        commit: Commit to compare (default: HEAD)

    Returns:
        List of NoteChange objects

    Raises:
        git.exc.InvalidGitRepositoryError: If not a valid git repo
        git.exc.GitCommandError: If git operations fail
    """
    repo = git.Repo(repo_path)
    head_commit = repo.commit(commit)

    # Check if there's a parent commit
    if not head_commit.parents:
        # Initial commit - treat all notes as added
        return _handle_initial_commit(repo_path, head_commit)

    parent_commit = head_commit.parents[0]

    # Find all deck.json files that changed
    changes = []
    for diff_item in parent_commit.diff(head_commit):
        if diff_item.b_path and 'deck.json' in diff_item.b_path:
            deck_changes = _compare_deck_versions(
                repo, diff_item.b_path, parent_commit, head_commit
            )
            changes.extend(deck_changes)

    return changes


def _handle_initial_commit(repo_path: str, commit: git.Commit) -> List[NoteChange]:
    """
    Handle initial commit where all notes are new.

    Args:
        repo_path: Repository path
        commit: The initial commit

    Returns:
        List of NoteChange objects with all notes marked as "added"
    """
    changes = []

    # Find all deck.json files in the commit
    for item in commit.tree.traverse():
        if item.name == 'deck.json' and item.type == 'blob':
            try:
                content = item.data_stream.read().decode('utf-8')
                deck, note_models = parse_deck_from_string(content)

                # Build note map
                note_map = build_note_map(deck)

                # Mark all notes as added
                for guid, (note, deck_path) in note_map.items():
                    if note.note_model_uuid in note_models:
                        note_model = note_models[note.note_model_uuid]
                        changes.append(NoteChange(
                            change_type="added",
                            after=note,
                            note_model=note_model,
                            deck_path=deck_path
                        ))
            except Exception as e:
                print(f"Warning: Failed to parse {item.path}: {e}")

    return changes


def _compare_deck_versions(
    repo: git.Repo,
    deck_path: str,
    before_commit: git.Commit,
    after_commit: git.Commit
) -> List[NoteChange]:
    """
    Compare two versions of a deck file.

    Args:
        repo: Git repository
        deck_path: Path to deck.json file
        before_commit: Earlier commit
        after_commit: Later commit

    Returns:
        List of NoteChange objects
    """
    changes = []

    try:
        # Load before version
        try:
            before_blob = before_commit.tree / deck_path
            before_content = before_blob.data_stream.read().decode('utf-8')
            before_deck, before_models = parse_deck_from_string(before_content)
        except KeyError:
            # File didn't exist in before commit (new file)
            before_deck = None
            before_models = {}

        # Load after version
        try:
            after_blob = after_commit.tree / deck_path
            after_content = after_blob.data_stream.read().decode('utf-8')
            after_deck, after_models = parse_deck_from_string(after_content)
        except KeyError:
            # File was deleted
            after_deck = None
            after_models = {}

        # If both are None, something went wrong
        if before_deck is None and after_deck is None:
            return changes

        # If only before exists, all notes deleted
        if before_deck and not after_deck:
            before_notes = build_note_map(before_deck)
            for guid, (note, deck_path_str) in before_notes.items():
                if note.note_model_uuid in before_models:
                    changes.append(NoteChange(
                        change_type="deleted",
                        before=note,
                        note_model=before_models[note.note_model_uuid],
                        deck_path=deck_path_str
                    ))
            return changes

        # If only after exists, all notes added
        if after_deck and not before_deck:
            after_notes = build_note_map(after_deck)
            for guid, (note, deck_path_str) in after_notes.items():
                if note.note_model_uuid in after_models:
                    changes.append(NoteChange(
                        change_type="added",
                        after=note,
                        note_model=after_models[note.note_model_uuid],
                        deck_path=deck_path_str
                    ))
            return changes

        # Both exist - compare notes
        before_notes = build_note_map(before_deck)
        after_notes = build_note_map(after_deck)

        # Detect additions and modifications
        for guid, (after_note, deck_path_str) in after_notes.items():
            # Get note model (prefer after version)
            note_model_uuid = after_note.note_model_uuid
            if note_model_uuid not in after_models:
                print(f"Warning: Note {guid} references unknown note model {note_model_uuid}")
                continue

            note_model = after_models[note_model_uuid]

            if guid not in before_notes:
                # New note
                changes.append(NoteChange(
                    change_type="added",
                    after=after_note,
                    note_model=note_model,
                    deck_path=deck_path_str
                ))
            else:
                # Check if modified
                before_note, _ = before_notes[guid]
                if not _notes_equal(before_note, after_note):
                    # Classify the change
                    content_type, details = classify_note_change(
                        before_note.fields,
                        after_note.fields
                    )

                    changes.append(NoteChange(
                        change_type="modified",
                        before=before_note,
                        after=after_note,
                        note_model=note_model,
                        deck_path=deck_path_str,
                        content_change_type=content_type,
                        cosmetic_changes=details.get("cosmetic_types", []),
                        classification_details=details
                    ))

        # Detect deletions
        for guid, (before_note, deck_path_str) in before_notes.items():
            if guid not in after_notes:
                # Deleted note
                note_model_uuid = before_note.note_model_uuid
                if note_model_uuid in before_models:
                    note_model = before_models[note_model_uuid]
                    changes.append(NoteChange(
                        change_type="deleted",
                        before=before_note,
                        note_model=note_model,
                        deck_path=deck_path_str
                    ))

    except Exception as e:
        print(f"Error comparing deck {deck_path}: {e}")

    return changes


def _notes_equal(note1: Note, note2: Note) -> bool:
    """
    Compare two notes for equality.

    Args:
        note1: First note
        note2: Second note

    Returns:
        True if notes are equal (same fields and tags)
    """
    return (note1.guid == note2.guid and
            note1.fields == note2.fields and
            sorted(note1.tags) == sorted(note2.tags) and
            note1.note_model_uuid == note2.note_model_uuid)


def get_commit_info(repo_path: str = ".", commit: str = "HEAD") -> Dict[str, str]:
    """
    Get commit information for display.

    Args:
        repo_path: Path to repository
        commit: Commit reference

    Returns:
        Dictionary with commit info (hash, message, author, date)
    """
    repo = git.Repo(repo_path)
    commit_obj = repo.commit(commit)

    return {
        "hash": commit_obj.hexsha[:8],
        "full_hash": commit_obj.hexsha,
        "message": commit_obj.message.strip(),
        "author": commit_obj.author.name,
        "email": commit_obj.author.email,
        "date": commit_obj.committed_datetime.isoformat()
    }
