"""Anki template rendering engine."""

import re
from typing import Dict, List


class AnkiTemplateEngine:
    """Render Anki card templates with field substitution."""

    def render(
        self,
        template: str,
        fields: Dict[str, str],
        tags: List[str] = None,
        is_answer: bool = False,
        front_side_html: str = ""
    ) -> str:
        """
        Render template with field values.

        Args:
            template: Template string (qfmt or afmt)
            fields: Dict mapping field names to values
            tags: List of note tags
            is_answer: True if rendering answer side
            front_side_html: Rendered front side (for {{FrontSide}})

        Returns:
            Rendered HTML string
        """
        if tags is None:
            tags = []

        result = template

        # Handle {{FrontSide}} - must be done first
        if is_answer and "{{FrontSide}}" in result:
            result = result.replace("{{FrontSide}}", front_side_html)

        # Handle {{Tags}}
        tags_str = " ".join(tags)
        result = result.replace("{{Tags}}", tags_str)

        # Handle cloze syntax {{cloze:FieldName}}
        result = self._render_cloze(result, fields)

        # Handle conditional blocks {{#Field}}...{{/Field}}
        result = self._render_conditionals(result, fields)

        # Handle simple field substitution {{FieldName}}
        result = self._render_fields(result, fields)

        return result

    def _render_cloze(self, template: str, fields: Dict[str, str]) -> str:
        """
        Render cloze deletions.

        Args:
            template: Template string
            fields: Field values

        Returns:
            Template with cloze fields rendered
        """
        def replace_cloze(match):
            field_name = match.group(1)
            field_value = fields.get(field_name, "")

            # Parse cloze syntax: {{c1::text}}, {{c2::text}}
            # For diff view, show all clozes revealed
            cloze_pattern = r'\{\{c(\d+)::([^}]+?)(?:::([^}]+))?\}\}'

            def replace_cloze_item(m):
                cloze_num = m.group(1)
                cloze_text = m.group(2)
                cloze_hint = m.group(3) or ""

                # Show the text revealed with styling
                return f'<span class="cloze" data-cloze="{cloze_num}">{cloze_text}</span>'

            return re.sub(cloze_pattern, replace_cloze_item, field_value)

        return re.sub(r'\{\{cloze:([^}]+)\}\}', replace_cloze, template)

    def _render_conditionals(self, template: str, fields: Dict[str, str]) -> str:
        """
        Render conditional blocks.

        Supports:
        - {{#Field}}content{{/Field}} - show if field non-empty
        - {{^Field}}content{{/Field}} - show if field empty

        Args:
            template: Template string
            fields: Field values

        Returns:
            Template with conditionals evaluated
        """
        # Handle negative conditionals first: {{^Field}}...{{/Field}}
        negative_pattern = r'\{\{\^([^}]+)\}\}(.*?)\{\{/\1\}\}'

        def replace_negative(match):
            field_name = match.group(1).strip()
            content = match.group(2)
            field_value = fields.get(field_name, "")

            # Show content if field is empty
            return content if not field_value.strip() else ""

        template = re.sub(negative_pattern, replace_negative, template, flags=re.DOTALL)

        # Handle positive conditionals: {{#Field}}...{{/Field}}
        positive_pattern = r'\{\{#([^}]+)\}\}(.*?)\{\{/\1\}\}'

        def replace_positive(match):
            field_name = match.group(1).strip()
            content = match.group(2)
            field_value = fields.get(field_name, "")

            # Show content if field is non-empty
            return content if field_value.strip() else ""

        return re.sub(positive_pattern, replace_positive, template, flags=re.DOTALL)

    def _render_fields(self, template: str, fields: Dict[str, str]) -> str:
        """
        Simple field substitution.

        Args:
            template: Template string
            fields: Field values

        Returns:
            Template with fields substituted
        """
        # Replace {{FieldName}} with field values
        for field_name, field_value in fields.items():
            # Escape field name for regex
            escaped_name = re.escape(field_name)
            template = re.sub(
                f'\\{{\\{{{escaped_name}\\}}\\}}',
                field_value,
                template
            )

        # Remove any unmatched field references (but preserve image-occlusion patterns)
        # Don't remove {{c1::image-occlusion:...}} patterns
        template = re.sub(
            r'\{\{(?!c\d+::image-occlusion)([^}]+)\}\}',
            '',
            template
        )

        return template

    def render_cloze_field_for_display(self, field_value: str, show_all: bool = True) -> str:
        """
        Render a cloze field value for display.

        Args:
            field_value: Field content with cloze deletions
            show_all: If True, show all clozes revealed

        Returns:
            HTML with cloze deletions rendered
        """
        if show_all:
            # Show all clozes revealed
            cloze_pattern = r'\{\{c(\d+)::([^}]+?)(?:::([^}]+))?\}\}'

            def replace_cloze(m):
                cloze_num = m.group(1)
                cloze_text = m.group(2)
                return f'<span class="cloze" data-cloze="{cloze_num}">{cloze_text}</span>'

            return re.sub(cloze_pattern, replace_cloze, field_value)
        else:
            # Show with hints only
            cloze_pattern = r'\{\{c(\d+)::([^}]+?)(?:::([^}]+))?\}\}'

            def replace_cloze(m):
                cloze_num = m.group(1)
                cloze_hint = m.group(3) or "[...]"
                return f'<span class="cloze-hidden" data-cloze="{cloze_num}">{cloze_hint}</span>'

            return re.sub(cloze_pattern, replace_cloze, field_value)


def extract_cloze_numbers(field_value: str) -> List[int]:
    """
    Extract cloze deletion numbers from a field value.

    Args:
        field_value: Field content

    Returns:
        List of cloze numbers (e.g., [1, 2, 3])
    """
    cloze_pattern = r'\{\{c(\d+)::'
    matches = re.findall(cloze_pattern, field_value)
    return sorted(set(int(num) for num in matches))


def has_cloze_deletions(field_value: str) -> bool:
    """
    Check if a field contains cloze deletions.

    Args:
        field_value: Field content

    Returns:
        True if field contains cloze deletions
    """
    return bool(re.search(r'\{\{c\d+::', field_value))
