"""HTML diff page generation."""

from pathlib import Path
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
import diff_match_patch as dmp_module

from .models import NoteChange, Note, NoteModel
from .template_engine import AnkiTemplateEngine
from .renderers import (
    BaseNoteRenderer,
    ClozeRenderer,
    BasicRenderer,
    ImageOcclusionRenderer,
    MultiFieldRenderer
)
from .media_handler import update_media_references_in_html


class HTMLDiffGenerator:
    """Generate HTML diff pages for note changes."""

    def __init__(self, template_dir: str = None):
        """
        Initialize HTML generator.

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        if template_dir is None:
            # Default to templates/ in src directory
            template_dir = Path(__file__).parent / "templates"

        self.template_dir = Path(template_dir)

        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Initialize template engine and renderers
        self.template_engine = AnkiTemplateEngine()
        self.renderers: List[BaseNoteRenderer] = [
            ImageOcclusionRenderer(self.template_engine),  # Check image occlusion first
            ClozeRenderer(self.template_engine),
            MultiFieldRenderer(self.template_engine),
            BasicRenderer(self.template_engine),
        ]

        # Initialize diff-match-patch for text diffing
        self.dmp = dmp_module.diff_match_patch()

    def generate_diff_page(
        self,
        changes: List[NoteChange],
        output_path: str,
        commit_info: Dict[str, str]
    ) -> None:
        """
        Generate HTML diff page.

        Args:
            changes: List of note changes
            output_path: Path to output HTML file
            commit_info: Dictionary with commit information
        """
        # Calculate statistics on all changes (including cosmetic)
        stats = self._calculate_stats(changes)

        # Filter out cosmetic-only changes from rendering
        # Keep: added, deleted, and content-modified notes
        # Remove: cosmetic-only modified notes
        changes_to_render = [
            change for change in changes
            if not change.is_cosmetic_only
        ]

        # Render filtered changes
        rendered_changes = []
        for change in changes_to_render:
            rendered_change = self._render_change(change)
            rendered_changes.append(rendered_change)

        # Load CSS
        css_file = self.template_dir / "styles.css"
        css_content = css_file.read_text(encoding='utf-8')

        # Load and render template
        template = self.jinja_env.get_template('diff_page.html.jinja2')
        html = template.render(
            changes=rendered_changes,
            commit_info=commit_info,
            stats=stats,
            css_content=css_content,
            total_changes=len(changes),
            rendered_count=len(changes_to_render)
        )

        # Write output
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html, encoding='utf-8')

    def _render_change(self, change: NoteChange) -> Dict[str, Any]:
        """
        Render a note change with before/after cards.

        Args:
            change: Note change to render

        Returns:
            Dictionary with rendered data
        """
        # Select appropriate renderer
        renderer = self._select_renderer(change.note_model)

        # Render before and after cards
        rendered_before = None
        rendered_after = None

        if change.before:
            rendered_before = renderer.render_card(change.before, change.note_model)
            # Update media paths
            rendered_before['front'] = update_media_references_in_html(rendered_before['front'])
            rendered_before['back'] = update_media_references_in_html(rendered_before['back'])

        if change.after:
            rendered_after = renderer.render_card(change.after, change.note_model)
            # Update media paths
            rendered_after['front'] = update_media_references_in_html(rendered_after['front'])
            rendered_after['back'] = update_media_references_in_html(rendered_after['back'])

        # Generate field-by-field diff
        field_diffs = self._generate_field_diffs(
            change.before,
            change.after,
            change.note_model
        )

        return {
            'change_type': change.change_type,
            'deck_path': change.deck_path,
            'guid': change.guid,
            'note_model': change.note_model,
            'before': change.before,
            'after': change.after,
            'rendered_before': rendered_before,
            'rendered_after': rendered_after,
            'field_diffs': field_diffs
        }

    def _select_renderer(self, note_model: NoteModel) -> BaseNoteRenderer:
        """
        Select appropriate renderer for note model.

        Args:
            note_model: Note model

        Returns:
            Renderer instance
        """
        for renderer in self.renderers:
            if renderer.can_render(note_model):
                return renderer

        # Fallback to basic renderer
        return self.renderers[-1]

    def _generate_field_diffs(
        self,
        before: Note,
        after: Note,
        note_model: NoteModel
    ) -> List[Dict[str, str]]:
        """
        Generate field-by-field diff.

        Args:
            before: Before note (or None)
            after: After note (or None)
            note_model: Note model

        Returns:
            List of field diff dictionaries
        """
        field_diffs = []

        for field_def in note_model.flds:
            before_value = ""
            after_value = ""

            if before and field_def.ord < len(before.fields):
                before_value = before.fields[field_def.ord]

            if after and field_def.ord < len(after.fields):
                after_value = after.fields[field_def.ord]

            # Only include if there's a difference
            if before_value != after_value:
                highlighted_before, highlighted_after = self._highlight_diff(before_value, after_value)
                field_diffs.append({
                    'name': field_def.name,
                    'before': highlighted_before,
                    'after': highlighted_after
                })

        return field_diffs

    def _highlight_diff(self, text1: str, text2: str) -> tuple[str, str]:
        """
        Highlight differences between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Tuple of (highlighted_text1, highlighted_text2)
        """
        diffs = self.dmp.diff_main(text1, text2)
        self.dmp.diff_cleanupSemantic(diffs)

        html1 = []
        html2 = []

        for op, text in diffs:
            escaped_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            if op == dmp_module.diff_match_patch.DIFF_DELETE:
                html1.append(f'<del>{escaped_text}</del>')
            elif op == dmp_module.diff_match_patch.DIFF_INSERT:
                html2.append(f'<ins>{escaped_text}</ins>')
            else:  # DIFF_EQUAL
                html1.append(escaped_text)
                html2.append(escaped_text)

        return ''.join(html1), ''.join(html2)

    def _calculate_stats(self, changes: List[NoteChange]) -> Dict[str, Any]:
        """
        Calculate change statistics including cosmetic changes.

        Args:
            changes: List of note changes

        Returns:
            Dictionary with counts and cosmetic statistics
        """
        from .change_classifier import ChangeType

        stats = {
            'added': 0,
            'modified': 0,
            'deleted': 0,
            'content_changes': 0,
            'cosmetic_only': 0,
            'cosmetic_breakdown': {
                ChangeType.WHITESPACE: 0,
                ChangeType.HTML_FORMATTING: 0,
                ChangeType.ENTITIES: 0,
                ChangeType.CASE: 0,
                ChangeType.PUNCTUATION: 0,
                ChangeType.MIXED_COSMETIC: 0
            }
        }

        for change in changes:
            # Count by change type
            if change.change_type in stats:
                stats[change.change_type] += 1

            # Count content vs cosmetic for modified notes
            if change.change_type == 'modified':
                if change.is_cosmetic_only:
                    stats['cosmetic_only'] += 1

                    # Count by specific cosmetic type
                    if change.content_change_type in stats['cosmetic_breakdown']:
                        stats['cosmetic_breakdown'][change.content_change_type] += 1
                else:
                    stats['content_changes'] += 1

        return stats


def generate_diff_html(
    changes: List[NoteChange],
    output_path: str,
    commit_info: Dict[str, str],
    template_dir: str = None
) -> None:
    """
    Convenience function to generate diff HTML.

    Args:
        changes: List of note changes
        output_path: Path to output HTML file
        commit_info: Commit information dictionary
        template_dir: Optional template directory
    """
    generator = HTMLDiffGenerator(template_dir)
    generator.generate_diff_page(changes, output_path, commit_info)
