"""Source-backed scholarship matrix for the active-inference exemplar.

Package layout (split 2026-06-10 from the former 1471-line ``scholarship.py``):

- ``schema``         — schema id + the closed expected-citation-key set
- ``sources_base``   — original authorship source batch (pure data)
- ``sources_review`` — RedTeam batch + 2026-06-10 external-review batch (pure data)
- ``matrix``         — builders, writers, validators (all logic)

Every symbol importable from the old module remains importable from
``roadmap_tracks.scholarship`` via the re-exports below.
"""

from __future__ import annotations

from .matrix import (
    SCHOLARSHIP_SOURCES,
    build_scholarship_source_matrix,
    validate_scholarship_source_matrix,
    validate_scholarship_source_matrix_payload,
    write_scholarship_source_matrix,
)
from .schema import EXPECTED_SCHOLARSHIP_KEYS, SCHOLARSHIP_SCHEMA
from .sources_base import _BASE_SCHOLARSHIP_SOURCES
from .sources_review import _REDTEAM_REVIEW_SOURCES, _RUN5_REVIEW_SOURCES

__all__ = [
    "EXPECTED_SCHOLARSHIP_KEYS",
    "SCHOLARSHIP_SCHEMA",
    "SCHOLARSHIP_SOURCES",
    "build_scholarship_source_matrix",
    "validate_scholarship_source_matrix",
    "validate_scholarship_source_matrix_payload",
    "write_scholarship_source_matrix",
]
