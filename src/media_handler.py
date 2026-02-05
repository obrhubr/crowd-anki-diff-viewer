"""Media file handling for crowd-anki decks."""

import re
import shutil
from pathlib import Path
from typing import List, Set
from .models import NoteChange


def copy_media_files(
    deck_path: str,
    output_dir: str,
    changes: List[NoteChange]
) -> Set[str]:
    """
    Copy all media files referenced in changed notes.

    Args:
        deck_path: Path to the deck.json file
        output_dir: Output directory for HTML
        changes: List of note changes

    Returns:
        Set of media filenames that were copied
    """
    deck_dir = Path(deck_path).parent
    media_source_dir = deck_dir / "media"

    output_path = Path(output_dir)
    media_output_dir = output_path / "media"

    # Create output media directory
    media_output_dir.mkdir(parents=True, exist_ok=True)

    # Collect all referenced media files
    media_files = set()

    for change in changes:
        # Check both before and after notes
        for note in [change.before, change.after]:
            if note:
                media_files.update(extract_media_from_note(note.fields))

    # Copy files
    copied_files = set()
    for filename in media_files:
        src = media_source_dir / filename
        dst = media_output_dir / filename

        if src.exists():
            try:
                shutil.copy2(src, dst)
                copied_files.add(filename)
            except Exception as e:
                print(f"Warning: Failed to copy media file {filename}: {e}")
        else:
            print(f"Warning: Media file not found: {filename}")

    return copied_files


def extract_media_from_note(fields: List[str]) -> Set[str]:
    """
    Extract media file references from note fields.

    Looks for:
    - <img src="filename.jpg">
    - [sound:filename.mp3]
    - Other common patterns

    Args:
        fields: List of field values

    Returns:
        Set of media filenames
    """
    media_files = set()

    for field in fields:
        # Extract image sources: <img src="filename.jpg">
        img_pattern = r'<img[^>]+src=["\'](.*?)["\']'
        for match in re.finditer(img_pattern, field, re.IGNORECASE):
            filename = match.group(1)
            # Remove any path components, keep just filename
            filename = Path(filename).name
            media_files.add(filename)

        # Extract sound files: [sound:filename.mp3]
        sound_pattern = r'\[sound:(.*?)\]'
        for match in re.finditer(sound_pattern, field):
            filename = match.group(1)
            media_files.add(filename)

        # Extract background images: url('filename.jpg')
        bg_pattern = r'url\(["\']?(.*?)["\']?\)'
        for match in re.finditer(bg_pattern, field):
            filename = match.group(1)
            filename = Path(filename).name
            media_files.add(filename)

    return media_files


def resolve_media_path(media_filename: str, base_path: str = "media") -> str:
    """
    Convert media filename to relative path for HTML.

    Args:
        media_filename: Name of media file
        base_path: Base path for media (default: "media")

    Returns:
        Relative path suitable for HTML
    """
    return f"{base_path}/{media_filename}"


def update_media_references_in_html(html: str, base_path: str = "media") -> str:
    """
    Update media references in HTML to use correct paths.

    Args:
        html: HTML content
        base_path: Base path for media files

    Returns:
        Updated HTML with corrected media paths
    """
    # Update img src attributes
    def replace_img_src(match):
        full_match = match.group(0)
        filename = match.group(1)
        # If it's just a filename (no path), prepend media path
        if '/' not in filename and not filename.startswith('http'):
            new_path = resolve_media_path(Path(filename).name, base_path)
            return full_match.replace(filename, new_path)
        return full_match

    html = re.sub(
        r'<img([^>]+)src=["\'](.*?)["\']',
        lambda m: f'<img{m.group(1)}src="{resolve_media_path(Path(m.group(2)).name, base_path)}"',
        html,
        flags=re.IGNORECASE
    )

    # Note: sound files and other media might need different handling
    # depending on how they're displayed

    return html


def get_media_mime_type(filename: str) -> str:
    """
    Get MIME type for a media file.

    Args:
        filename: Media filename

    Returns:
        MIME type string
    """
    ext = Path(filename).suffix.lower()

    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
    }

    return mime_types.get(ext, 'application/octet-stream')
