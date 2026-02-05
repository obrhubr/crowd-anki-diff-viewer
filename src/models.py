"""Data models for crowd-anki deck structures."""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import IntEnum


class NoteType(IntEnum):
    """Note type enumeration matching Anki's values."""
    BASIC = 0
    CLOZE = 1


class FieldModel(BaseModel):
    """Represents a field definition in a note model."""
    name: str
    ord: int
    font: str = "Arial"
    size: int = 20
    sticky: bool = False
    rtl: bool = False
    collapsed: bool = False
    description: str = ""
    excludeFromSearch: bool = False
    plainText: bool = False
    preventDeletion: bool = False
    media: List[str] = []
    tag: Optional[Any] = None  # Can be string or int
    id: Optional[int] = None


class Template(BaseModel):
    """Represents a card template in a note model."""
    name: str
    ord: int
    qfmt: str  # Question format (front of card)
    afmt: str  # Answer format (back of card)
    bqfmt: str = ""  # Browser question format
    bafmt: str = ""  # Browser answer format
    bfont: str = ""
    bsize: int = 0
    did: Optional[int] = None
    id: Optional[int] = None


class NoteModel(BaseModel):
    """Represents a note model (card type) definition."""
    crowdanki_uuid: str
    name: str
    type: NoteType
    flds: List[FieldModel]
    tmpls: List[Template]
    css: str
    latexPre: str = ""
    latexPost: str = ""
    latexsvg: bool = False
    req: List[Any] = []
    sortf: int = 0
    did: Optional[int] = None
    mod: int = 0
    tags: List[str] = []
    usn: int = -1
    vers: List[Any] = []
    originalId: Optional[int] = None
    originalStockKind: Optional[int] = None


class Note(BaseModel):
    """Represents a single note (flashcard)."""
    __type__: str = "Note"
    guid: str
    note_model_uuid: str
    fields: List[str]
    tags: List[str] = []

    def __eq__(self, other: object) -> bool:
        """Compare notes based on fields and tags."""
        if not isinstance(other, Note):
            return False
        return (self.guid == other.guid and
                self.fields == other.fields and
                self.tags == other.tags)

    def __hash__(self) -> int:
        """Hash based on guid."""
        return hash(self.guid)


class Deck(BaseModel):
    """Represents a deck (can be hierarchical with children)."""
    __type__: str = "Deck"
    name: str
    crowdanki_uuid: str
    notes: List[Note] = []
    children: List['Deck'] = []
    media_files: List[str] = []
    deck_config_uuid: Optional[str] = None
    desc: str = ""
    dyn: int = 0
    extendNew: int = 0
    extendRev: int = 0
    newLimit: Optional[int] = None
    newLimitToday: Optional[int] = None
    reviewLimit: Optional[int] = None
    reviewLimitToday: Optional[int] = None
    desiredRetention: Optional[float] = None
    mid: Optional[int] = None  # Some decks have this field

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


class NoteChange(BaseModel):
    """Represents a change to a note between two versions."""
    change_type: str  # "added", "modified", "deleted"
    before: Optional[Note] = None
    after: Optional[Note] = None
    note_model: NoteModel
    deck_path: str  # e.g., "ETH::1. Semester::A&D"

    # Classification of change content
    content_change_type: str = "content"  # "content", "whitespace", "html_formatting", etc.
    cosmetic_changes: List[str] = []  # List of specific cosmetic changes detected
    classification_details: Dict[str, Any] = {}  # Detailed classification info

    @property
    def guid(self) -> str:
        """Get the GUID of the changed note."""
        if self.after:
            return self.after.guid
        elif self.before:
            return self.before.guid
        return "unknown"

    @property
    def is_cosmetic_only(self) -> bool:
        """Check if this is a cosmetic-only change."""
        return self.content_change_type != "content"
