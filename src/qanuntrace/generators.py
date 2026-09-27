"""Generator adapters accept structured JSON proposals, never text-only legal answers.

These are transport wrappers; validate each provider/version in the team's environment.
User prompts and retrieved text may be sent to a remote provider when configured.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import Any

from .types import EvidenceProposal, LegalRecord, Query

SYSTEM = ("Return only JSON: an array of objects with keys source_id, instrument_id, "
          "edition_id, reference, start, end, proposed_quote, and optional interpretation, "
          "linked_article_source_id, relation. Offsets are Python Unicode character offsets "
          "in the provided exact_text. Never invent a record or quote. If uncertain return [].")

def payload(query: Query, records: tuple[LegalRecord, ...]) -> str:
    return json.dumps({"question": query.text,
                       "records": [{"source_id": r.source_id, "instrument_id": r.instrument_id,
                                    "edition_id": r.edition_id, "reference": r.reference,
                                    "kind": r.kind, "exact_text": r.exact_text}
                                   for r in records]}, ensure_ascii=False)

def parse_proposals(text: str) -> tuple[EvidenceProposal, ...]:
    data = json.loads(text)
    if not isinstance(data, list) or len(data) > 100:
        raise ValueError("expected JSON array of <=100 proposals")
    required = ("source_id", "instrument_id", "edition_id", "reference",
                "start", "end", "proposed_quote")
    output = []
    for item in data:
        if not isinstance(item, dict) or any(k not in item for k in required):
            raise ValueError("invalid proposal")
        if type(item["start"]) is not int or type(item["end"]) is not int:
            raise ValueError("offsets must be integers")
        output.append(EvidenceProposal(**{k: item[k] for k in
                      (*required, "interpretation", "linked_article_source_id", "relation") if k in item}))
    return tuple(output)

class CallableGenerator:
    def __init__(self, call: Callable[[str, str], str]): self.call = call
    def propose(self, query: Query, records: tuple[LegalRecord, ...]) -> Iterable[EvidenceProposal]:
        return parse_proposals(self.call(SYSTEM, payload(query, records)))

class OpenAICompatibleGenerator(CallableGenerator):
    """OpenAI SDK chat completions; accepts a configured base_url for local compatible servers."""
    def __init__(self, client: Any, model: str):
        def call(system: str, user: str) -> str:
            response = client.chat.completions.create(model=model, temperature=0,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
            return response.choices[0].message.content or "[]"
        super().__init__(call)

class AnthropicGenerator(CallableGenerator):
    def __init__(self, client: Any, model: str, max_tokens: int = 2000):
        def call(system: str, user: str) -> str:
            response = client.messages.create(model=model, max_tokens=max_tokens, temperature=0,
                                               system=system, messages=[{"role": "user", "content": user}])
            return "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
        super().__init__(call)

class GoogleGenerator(CallableGenerator):
    def __init__(self, client: Any, model: str):
        def call(system: str, user: str) -> str:
            response = client.models.generate_content(model=model, contents=system + "\n" + user,
                                                       config={"temperature": 0})
            return response.text or "[]"
        super().__init__(call)
