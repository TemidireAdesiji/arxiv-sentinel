"""Pure domain objects — no framework dependencies."""

from sentinel.domain.chunk import TextFragment
from sentinel.domain.paper import PaperRecord

__all__ = ["PaperRecord", "TextFragment"]
