"""Renderer for complex multi-field cards."""

from typing import Dict
from ..models import Note, NoteModel, NoteType
from .base import BaseNoteRenderer


class MultiFieldRenderer(BaseNoteRenderer):
    """
    Renderer for multi-field cards (like algorithm cards with multiple templates).

    This handles cards that have many fields (e.g., Name, Runtime, Requirements,
    Approach, etc.) and potentially multiple card templates.
    """

    def can_render(self, note_model: NoteModel) -> bool:
        """
        Check if this is a multi-field note model.

        We consider it multi-field if it has:
        - More than 3 fields, OR
        - Multiple templates (more than 1)

        Args:
            note_model: Note model to check

        Returns:
            True if this is a multi-field model
        """
        # Multi-field models typically have many fields or multiple templates
        return (len(note_model.flds) > 3 or len(note_model.tmpls) > 1) and \
               note_model.type == NoteType.BASIC

    def render_card(
        self,
        note: Note,
        note_model: NoteModel,
        template_idx: int = 0
    ) -> Dict[str, str]:
        """
        Render a multi-field card.

        Args:
            note: Note to render
            note_model: Note model with templates
            template_idx: Template index to use

        Returns:
            Dictionary with "front", "back", "css", and "template_name" keys
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
            "template_name": template.name,
            "template_index": template_idx,
            "total_templates": len(note_model.tmpls)
        }
