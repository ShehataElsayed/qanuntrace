import json

import pytest

from qanuntrace import EvidenceProposal, LegalRecord, Pipeline, Query, reference_key, verify
from qanuntrace.adapters import JSONLStore, MemoryStore, SearchStore, VectorStore
from qanuntrace.generators import CallableGenerator, parse_proposals


@pytest.fixture
def r():
    return LegalRecord.make("L1", "synthetic", "v2", "article", "١٢",
                            "لا يجوز الجمع بين الأمرين.", "fixture:local",
                            effective_from="2025-01-01", effective_to="2027-01-01")

def proposal(r, **changes):
    base = {"source_id": r.source_id, "instrument_id": r.instrument_id,
                "edition_id": r.edition_id, "reference": "12", "start": 0,
                "end": len(r.exact_text), "proposed_quote": r.exact_text}
    base.update(changes)
    return EvidenceProposal(**base)

@pytest.mark.parametrize("number", ["12", "١٢", "۱۲", "0012"])
def test_numerals(number): assert reference_key(number) == "12"

def test_exact_quote(r):
    result = verify(MemoryStore([r]), Query("test", as_of="2026-01-01"), proposal(r))
    assert result.status == "verified_quote" and result.quote == r.exact_text

@pytest.mark.parametrize("change,reason", [
    ({"reference": "13"}, "source_identity_mismatch"),
    ({"edition_id": "v1"}, "source_identity_mismatch"),
    ({"proposed_quote": "يجوز الجمع بين الأمرين."}, "quote_mismatch"),
    ({"source_id": "fake"}, "unknown_source_id"),
    ({"start": -1}, "invalid_span"),
])
def test_fail_closed(r, change, reason):
    assert verify(MemoryStore([r]), Query("test"), proposal(r, **change)).reason == reason

def test_temporal_unknown_and_expired(r):
    assert verify(MemoryStore([r]), Query("x", as_of="2024-01-01"), proposal(r)).status == "rejected"
    unknown = LegalRecord.make("L2", "synthetic", "v2", "article", "12", "x", "fixture:local")
    assert verify(MemoryStore([unknown]), Query("x", as_of="2026-01-01"),
                  proposal(unknown)).status == "needs_review"

def test_interpretation_and_judgment_links(r):
    assert verify(MemoryStore([r]), Query("x"), proposal(r, interpretation="conclusion")).status == "needs_review"
    judgment = LegalRecord.make("J1", "court-a", "v1", "judgment", "99",
                                "ذُكرت المادة ١٢ في الحكم.", "fixture:judgment")
    store = MemoryStore([r, judgment])
    p = proposal(judgment, reference="99", linked_article_source_id="L1", relation="applies")
    assert verify(store, Query("x"), p).reason == "judgment_relation_needs_review"
    assert verify(store, Query("x"), proposal(judgment, reference="99",
                  linked_article_source_id="missing", relation="applies")).status == "rejected"

def test_access_and_hash(r):
    restricted = LegalRecord.make("R", "syn", "v1", "article", "1", "secret", "fixture:local", access_label="team")
    assert verify(MemoryStore([restricted]), Query("x"), proposal(restricted, reference="1")).reason == "access_denied"
    assert verify(MemoryStore([restricted]), Query("x", access_labels=frozenset({"team"})),
                  proposal(restricted, reference="1")).status == "verified_quote"
    tampered = LegalRecord("L1", "synthetic", "v2", "article", "١٢", "changed", "fixture:local", r.source_hash)
    assert verify(MemoryStore([tampered]), Query("x"), proposal(r)).reason == "source_hash_mismatch"

def test_pipeline_repairs_by_exclusion(r):
    def call(system, user):
        return json.dumps([{"source_id": "L1", "instrument_id": "synthetic", "edition_id": "v2",
                                "reference": "12", "start": 0, "end": len(r.exact_text), "proposed_quote": r.exact_text},
                           {"source_id": "fake", "instrument_id": "synthetic", "edition_id": "v2",
                                "reference": "12", "start": 0, "end": 1, "proposed_quote": "x"}])
    answer = Pipeline(MemoryStore([r]), CallableGenerator(call)).answer(Query("الجمع"))
    assert answer.status == "verified_quote" and len(answer.findings) == 2
    assert "fake" not in answer.text and r.exact_text in answer.text
    assert [a.stage for a in answer.audit] == ["understand", "retrieve", "rerank", "generate",
                                                 "verify", "verify", "repair"]

def test_pipeline_abstains_no_match(r):
    assert Pipeline(MemoryStore([r]), CallableGenerator(lambda *_: "[]")).answer(
        Query("x", instrument_id="other")).status == "abstained"

def test_jsonl_file(tmp_path, r):
    path = tmp_path / "sources.jsonl"
    path.write_text(json.dumps(r.__dict__, ensure_ascii=False) + "\n", encoding="utf-8")
    assert JSONLStore(path).get("L1") == r

def test_vector_hydrates_canonical_source(r):
    store = VectorStore(lambda text, limit: ["L1", "fake"], MemoryStore([r]))
    assert list(store.search(Query("الجمع"), 2)) == [r]

class FakeSearch:
    def __init__(self, record): self.record = record
    def get(self, **kw): return {"_source": self.record.__dict__}
    def search(self, **kw): return {"hits": {"hits": [{"_source": self.record.__dict__}]}}

def test_search_adapter(r):
    store = SearchStore(FakeSearch(r), "idx", lambda row: LegalRecord(**row))
    assert list(store.search(Query("الجمع"), 2)) == [r]

def test_malformed_output():
    with pytest.raises((ValueError, TypeError)):
        parse_proposals('{"answer": "made up"}')
