"""Curated legal concepts are search expansions only, never legal equivalence."""
from __future__ import annotations

from dataclasses import dataclass

from .core import search_key


@dataclass(frozen=True)
class Concept:
    concept_id: str
    preferred_term: str
    search_aliases: tuple[str, ...]
    reviewed_by: str
    reviewed_at: str


class CuratedOntology:
    def __init__(self, concepts: tuple[Concept, ...]):
        self.lookup: dict[str, str] = {}
        for concept in concepts:
            if not all((concept.concept_id, concept.preferred_term,
                        concept.reviewed_by, concept.reviewed_at)):
                raise ValueError("concept needs stable ID and reviewer provenance")
            for term in (concept.preferred_term, *concept.search_aliases):
                key = search_key(term)
                if not key or (key in self.lookup and self.lookup[key] != concept.concept_id):
                    raise ValueError("ambiguous or blank concept alias")
                self.lookup[key] = concept.concept_id

    def candidates(self, query: str) -> tuple[str, ...]:
        """Return exact alias candidate IDs; never rewrite legal quotations."""
        normalized = search_key(query)
        return tuple(dict.fromkeys(cid for alias, cid in self.lookup.items()
                                   if alias == normalized or alias in normalized.split()))
