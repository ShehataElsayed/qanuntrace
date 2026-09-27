"""Evidence-backed graph expansion. Candidate relationships remain review-only."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal

from .core import LegalStore
from .types import LegalRecord

EdgeKind = Literal['amends','implements','cites','applies','distinguishes','mentions','related_concept']

@dataclass(frozen=True)
class Edge:
    source_id: str
    target_id: str
    relation: EdgeKind
    evidence_source_id: str
    evidence_start: int
    evidence_end: int
    evidence_quote: str
    reviewed_by: str | None = None

class EvidenceGraph:
    def __init__(self, store: LegalStore):
        self.store = store
        self.edges: dict[str, list[Edge]] = {}

    def add(self, edge: Edge) -> None:
        source = self.store.get(edge.source_id)
        target = self.store.get(edge.target_id)
        evidence = self.store.get(edge.evidence_source_id)
        if not source or not target or not evidence:
            raise ValueError('all nodes and evidence must exist in authoritative store')
        if (edge.evidence_start < 0 or edge.evidence_end <= edge.evidence_start
            or edge.evidence_end > len(evidence.exact_text)
            or evidence.exact_text[edge.evidence_start:edge.evidence_end] != edge.evidence_quote):
            raise ValueError('edge evidence must be an exact span')
        if not edge.reviewed_by and edge.relation not in ('mentions',):
            raise ValueError('substantive relations need human review')
        self.edges.setdefault(edge.source_id, []).append(edge)

    def expand(self, seed: str, max_hops: int = 2, max_nodes: int = 100,
               reviewed_only: bool = True) -> tuple[LegalRecord, ...]:
        if max_hops < 0 or max_hops > 5 or not 1 <= max_nodes <= 1000:
            raise ValueError('unsafe expansion bounds')
        seen: set[str] = set()
        queue = deque([(seed, 0)])
        out: list[LegalRecord] = []
        while queue and len(out) < max_nodes:
            source_id, depth = queue.popleft()
            if source_id in seen:
                continue
            seen.add(source_id)
            record = self.store.get(source_id)
            if record is None:
                continue
            out.append(record)
            if depth < max_hops:
                for edge in self.edges.get(source_id, ()):
                    if reviewed_only and not edge.reviewed_by:
                        continue
                    evidence = self.store.get(edge.evidence_source_id)
                    if evidence and evidence.exact_text[edge.evidence_start:edge.evidence_end] == edge.evidence_quote:
                        queue.append((edge.target_id, depth + 1))
        return tuple(out)
