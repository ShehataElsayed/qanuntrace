"""Provider-neutral proposal bridge; arbitrary API/local models use caller adapters."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Protocol

from .generators import SYSTEM, parse_proposals, payload
from .types import EvidenceProposal, LegalRecord, Query


class TextModel(Protocol):
    def complete(self, system: str, user: str) -> str: ...

@dataclass(frozen=True)
class FunctionModel:
    """Wrap any local model or API client in a two-string callable."""
    call: Callable[[str, str], str]

    def complete(self, system: str, user: str) -> str:
        return self.call(system, user)


class ProposalBridge:
    """Model output is only proposals; Pipeline verifies against the source store."""
    def __init__(self, model: TextModel, *, approve_transfer: Callable[[Query, tuple[LegalRecord, ...]], bool],
                 max_records: int = 20, max_chars: int = 100_000):
        if not 1 <= max_records <= 1000 or not 1 <= max_chars <= 2_000_000:
            raise ValueError('invalid model context limits')
        self.model, self.approve_transfer = model, approve_transfer
        self.max_records, self.max_chars = max_records, max_chars

    def propose(self, query: Query, records: tuple[LegalRecord, ...]) -> Iterable[EvidenceProposal]:
        if len(records) > self.max_records or sum(len(r.exact_text) for r in records) > self.max_chars:
            raise ValueError('model context limit exceeded; narrow retrieval')
        if not self.approve_transfer(query, records):
            raise PermissionError('model transfer denied by deployment policy')
        return parse_proposals(self.model.complete(SYSTEM, payload(query, records)))
