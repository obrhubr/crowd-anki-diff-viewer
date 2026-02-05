"""Base renderer for note cards."""

from abc import ABC, abstractmethod
from typing import Dict
from ..models import Note, NoteModel
from ..template_engine import AnkiTemplateEngine


class BaseNoteRenderer(ABC):
    """Abstract base class for note renderers."""

    def __init__(self, template_engine: AnkiTemplateEngine):
        """
        Initialize renderer.

        Args:
            template_engine: Template engine for rendering
        """
        self.template_engine = template_engine

    @abstractmethod
    def can_render(self, note_model: NoteModel) -> bool:
        """
        Check if this renderer can handle the note model.

        Args:
            note_model: Note model to check

        Returns:
            True if this renderer can handle this note type
        """
        pass

    @abstractmethod
    def render_card(
        self,
        note: Note,
        note_model: NoteModel,
        template_idx: int = 0
    ) -> Dict[str, str]:
        """
        Render a card and return front/back HTML.

        Args:
            note: Note to render
            note_model: Note model with templates
            template_idx: Index of template to use (for multi-template models)

        Returns:
            Dictionary with keys: "front", "back", "css"
        """
        pass

    def _build_field_map(self, note: Note, note_model: NoteModel) -> Dict[str, str]:
        """
        Build a dictionary mapping field names to values.

        Args:
            note: Note with field values
            note_model: Note model with field definitions

        Returns:
            Dictionary mapping field names to values
        """
        field_map = {}

        for field_def in note_model.flds:
            # Get value by ordinal
            if field_def.ord < len(note.fields):
                field_map[field_def.name] = note.fields[field_def.ord]
            else:
                field_map[field_def.name] = ""

        return field_map

    def render_all_cards(
        self,
        note: Note,
        note_model: NoteModel
    ) -> list[Dict[str, str]]:
        """
        Render all cards for a note (useful for multi-template models).

        Args:
            note: Note to render
            note_model: Note model with templates

        Returns:
            List of dictionaries, one per card template
        """
        cards = []
        for i in range(len(note_model.tmpls)):
            card = self.render_card(note, note_model, template_idx=i)
            cards.append(card)
        return cards
