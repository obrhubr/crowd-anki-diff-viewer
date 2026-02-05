"""Renderer for basic front/back cards."""

from typing import Dict
from ..models import Note, NoteModel, NoteType
from .base import BaseNoteRenderer


class BasicRenderer(BaseNoteRenderer):
    """Renderer for basic front/back cards."""

    def can_render(self, note_model: NoteModel) -> bool:
        """Check if this is a basic note model."""
        return note_model.type == NoteType.BASIC

    def render_card(
        self,
        note: Note,
        note_model: NoteModel,
        template_idx: int = 0
    ) -> Dict[str, str]:
        """
        Render a basic card.

        Args:
            note: Note to render
            note_model: Note model with templates
            template_idx: Template index

        Returns:
            Dictionary with "front", "back", and "css" keys
        """
        if template_idx >= len(note_model.tmpls):
            template_idx = 0

        template = note_model.tmpls[template_idx]

        # Build field map
        fields = self._build_field_map(note, note_model)

        # Render front (question)
        front_html = self.template_engine.render(
            template.qfmt,
            fields,
            note.tags,
            is_answer=False
        )

        # Render back (answer)
        back_html = self.template_engine.render(
            template.afmt,
            fields,
            note.tags,
            is_answer=True,
            front_side_html=front_html
        )

        return {
            "front": front_html,
            "back": back_html,
            "css": note_model.css,
            "template_name": template.name
        }
