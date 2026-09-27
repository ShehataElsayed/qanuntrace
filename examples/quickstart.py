"""Synthetic end-to-end demo. No legal corpus, credentials, or network access."""
import json

from qanuntrace import LegalRecord, Pipeline, Query
from qanuntrace.adapters import MemoryStore
from qanuntrace.generators import CallableGenerator

record = LegalRecord.make(
    "sample-1", "synthetic-law", "v1", "article", "1",
    "لا يجوز تغيير النص التجريبي.", "fixture:local",
)


def propose(_system: str, _user: str) -> str:
    """A fixed stand-in for a model; it proposes a source span, not legal advice."""
    return json.dumps([{
        "source_id": record.source_id,
        "instrument_id": record.instrument_id,
        "edition_id": record.edition_id,
        "reference": record.reference,
        "start": 0,
        "end": len(record.exact_text),
        "proposed_quote": record.exact_text,
    }], ensure_ascii=False)


answer = Pipeline(MemoryStore([record]), CallableGenerator(propose)).answer(
    Query("النص التجريبي", instrument_id="synthetic-law", reference="1")
)
print(answer.status)
print(answer.text)
