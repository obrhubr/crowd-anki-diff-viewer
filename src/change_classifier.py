"""Classifier for detecting non-visible changes in notes."""

import re
from typing import List, Set, Tuple
from html import unescape
from bs4 import BeautifulSoup


class ChangeType:
    """Types of changes detected."""
    CONTENT = "content"  # Actual content changed
    WHITESPACE = "whitespace"  # Only whitespace changed
    HTML_FORMATTING = "html_formatting"  # HTML tags/attributes changed but not content
    ENTITIES = "entities"  # HTML entities changed (nbsp, etc)
    CASE = "case"  # Only letter case changed
    PUNCTUATION = "punctuation"  # Only punctuation/symbols changed
    MIXED_COSMETIC = "mixed_cosmetic"  # Multiple cosmetic changes


class ChangeClassifier:
    """Classifies changes as visible or non-visible."""

    # HTML entities that are effectively whitespace
    WHITESPACE_ENTITIES = {
        '&nbsp;', '&ensp;', '&emsp;', '&thinsp;',
        '&#160;', '&#8194;', '&#8195;', '&#8201;'
    }

    # HTML tags that don't affect content
    FORMATTING_ONLY_TAGS = {
        'span', 'div', 'font', 'b', 'i', 'u', 'strong', 'em',
        'sup', 'sub', 'mark', 'small', 'big', 'center'
    }

    def __init__(self):
        """Initialize classifier."""
        pass

    def classify_field_change(self, before: str, after: str) -> Tuple[str, List[str]]:
        """
        Classify a field change.

        Args:
            before: Previous field value
            after: New field value

        Returns:
            Tuple of (change_type, list of specific changes detected)
        """
        if before == after:
            return ChangeType.CONTENT, []

        changes_detected = []

        # Normalize and compare
        before_normalized = self._normalize_for_comparison(before)
        after_normalized = self._normalize_for_comparison(after)

        if before_normalized == after_normalized:
            # Content is the same, only formatting differs
            changes_detected = self._detect_cosmetic_changes(before, after)

            if len(changes_detected) == 1:
                return changes_detected[0], changes_detected
            elif len(changes_detected) > 1:
                return ChangeType.MIXED_COSMETIC, changes_detected
            else:
                # Shouldn't happen, but fallback
                return ChangeType.HTML_FORMATTING, ["unknown"]

        # Content actually changed
        return ChangeType.CONTENT, []

    def _normalize_for_comparison(self, text: str) -> str:
        """
        Normalize text for comparison, removing all non-visible differences.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Parse HTML and get text content
        try:
            soup = BeautifulSoup(text, 'html.parser')
            text_content = soup.get_text()
        except:
            text_content = text

        # Decode HTML entities
        text_content = unescape(text_content)

        # Replace various whitespace characters with single space
        text_content = re.sub(r'\s+', ' ', text_content)

        # Remove leading/trailing whitespace
        text_content = text_content.strip()

        # Convert to lowercase for case-insensitive comparison
        # (we'll check case separately)
        text_content = text_content.lower()

        return text_content

    def _detect_cosmetic_changes(self, before: str, after: str) -> List[str]:
        """
        Detect specific types of cosmetic changes.

        Args:
            before: Before text
            after: After text

        Returns:
            List of change types detected
        """
        changes = []

        # Check for whitespace-only changes first
        # If only whitespace changed, don't check other conditions
        if self._is_whitespace_change(before, after):
            return [ChangeType.WHITESPACE]

        # Check for HTML entity changes
        if self._is_entity_change(before, after):
            changes.append(ChangeType.ENTITIES)

        # Check for HTML formatting changes
        if self._is_html_formatting_change(before, after):
            changes.append(ChangeType.HTML_FORMATTING)

        # Check for case changes
        if self._is_case_change(before, after):
            changes.append(ChangeType.CASE)

        # Check for punctuation changes
        if self._is_punctuation_change(before, after):
            changes.append(ChangeType.PUNCTUATION)

        # If nothing detected but we know they're different, it's HTML formatting
        if not changes:
            changes.append(ChangeType.HTML_FORMATTING)

        return changes

    def _is_whitespace_change(self, before: str, after: str) -> bool:
        """Check if only whitespace changed."""
        # Remove all whitespace and compare
        before_no_ws = re.sub(r'\s+', '', before)
        after_no_ws = re.sub(r'\s+', '', after)

        # Also remove HTML whitespace entities
        for entity in self.WHITESPACE_ENTITIES:
            before_no_ws = before_no_ws.replace(entity, '')
            after_no_ws = after_no_ws.replace(entity, '')

        return before_no_ws == after_no_ws

    def _is_entity_change(self, before: str, after: str) -> bool:
        """Check if HTML entities changed."""
        # Count HTML entities
        before_entities = set(re.findall(r'&[a-zA-Z]+;|&#\d+;', before))
        after_entities = set(re.findall(r'&[a-zA-Z]+;|&#\d+;', after))

        # If entity count differs, it's an entity change
        if before_entities != after_entities:
            # But only if the decoded versions are the same
            before_decoded = unescape(before)
            after_decoded = unescape(after)
            return self._normalize_for_comparison(before_decoded) == \
                   self._normalize_for_comparison(after_decoded)

        return False

    def _is_html_formatting_change(self, before: str, after: str) -> bool:
        """Check if only HTML formatting changed."""
        try:
            before_soup = BeautifulSoup(before, 'html.parser')
            after_soup = BeautifulSoup(after, 'html.parser')

            # Get text content (no tags)
            before_text = before_soup.get_text()
            after_text = after_soup.get_text()

            # Normalize whitespace in text
            before_text = re.sub(r'\s+', ' ', before_text).strip()
            after_text = re.sub(r'\s+', ' ', after_text).strip()

            # If text is the same but HTML differs, it's formatting
            return before_text == after_text and before != after

        except:
            return False

    def _is_case_change(self, before: str, after: str) -> bool:
        """Check if only letter case changed."""
        # Remove HTML tags for fair comparison
        try:
            before_soup = BeautifulSoup(before, 'html.parser')
            after_soup = BeautifulSoup(after, 'html.parser')
            before_text = before_soup.get_text()
            after_text = after_soup.get_text()
        except:
            before_text = before
            after_text = after

        # Normalize whitespace
        before_text = re.sub(r'\s+', ' ', before_text).strip()
        after_text = re.sub(r'\s+', ' ', after_text).strip()

        # Check if only case differs
        return before_text.lower() == after_text.lower() and before_text != after_text

    def _is_punctuation_change(self, before: str, after: str) -> bool:
        """Check if only punctuation changed."""
        # Remove all punctuation and compare
        punctuation_pattern = r'[^\w\s]'

        try:
            before_soup = BeautifulSoup(before, 'html.parser')
            after_soup = BeautifulSoup(after, 'html.parser')
            before_text = before_soup.get_text()
            after_text = after_soup.get_text()
        except:
            before_text = before
            after_text = after

        before_no_punct = re.sub(punctuation_pattern, '', before_text)
        after_no_punct = re.sub(punctuation_pattern, '', after_text)

        # Normalize whitespace
        before_no_punct = re.sub(r'\s+', ' ', before_no_punct).strip()
        after_no_punct = re.sub(r'\s+', ' ', after_no_punct).strip()

        return before_no_punct.lower() == after_no_punct.lower() and \
               before_text != after_text


def classify_note_change(before_fields: List[str], after_fields: List[str]) -> Tuple[str, dict]:
    """
    Classify all field changes in a note.

    Args:
        before_fields: List of field values before
        after_fields: List of field values after

    Returns:
        Tuple of (overall_change_type, details_dict)
    """
    classifier = ChangeClassifier()

    field_changes = {}
    cosmetic_types = set()
    has_content_change = False

    max_len = max(len(before_fields), len(after_fields))

    for i in range(max_len):
        before_val = before_fields[i] if i < len(before_fields) else ""
        after_val = after_fields[i] if i < len(after_fields) else ""

        if before_val != after_val:
            change_type, details = classifier.classify_field_change(before_val, after_val)
            field_changes[f"field_{i}"] = {
                "type": change_type,
                "details": details
            }

            if change_type == ChangeType.CONTENT:
                has_content_change = True
            else:
                cosmetic_types.update(details)

    # Determine overall change type
    if has_content_change:
        overall_type = ChangeType.CONTENT
    elif len(cosmetic_types) == 1:
        overall_type = list(cosmetic_types)[0]
    elif len(cosmetic_types) > 1:
        overall_type = ChangeType.MIXED_COSMETIC
    else:
        overall_type = ChangeType.CONTENT  # Fallback

    return overall_type, {
        "field_changes": field_changes,
        "cosmetic_types": list(cosmetic_types)
    }


def get_change_description(change_type: str, cosmetic_types: List[str] = None) -> str:
    """
    Get human-readable description of change type.

    Args:
        change_type: Type of change
        cosmetic_types: List of specific cosmetic changes (if applicable)

    Returns:
        Human-readable description
    """
    descriptions = {
        ChangeType.CONTENT: "Content changed",
        ChangeType.WHITESPACE: "Whitespace only",
        ChangeType.HTML_FORMATTING: "HTML formatting only",
        ChangeType.ENTITIES: "HTML entities only",
        ChangeType.CASE: "Letter case only",
        ChangeType.PUNCTUATION: "Punctuation only",
        ChangeType.MIXED_COSMETIC: "Cosmetic changes only"
    }

    base_desc = descriptions.get(change_type, "Changed")

    if cosmetic_types and len(cosmetic_types) > 1:
        types_desc = ", ".join([descriptions.get(t, t) for t in cosmetic_types])
        return f"{base_desc} ({types_desc})"

    return base_desc
