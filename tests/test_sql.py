import pytest

sa = pytest.importorskip("sqlalchemy")
from qanuntrace import LegalRecord, Query
from qanuntrace.adapters import SQLAlchemyStore


def test_sqlite_roundtrip():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    meta = sa.MetaData()
    t = sa.Table("records", meta, *[sa.Column(name, sa.String, primary_key=(name == "source_id"))
                                    for name in ["source_id", "instrument_id", "edition_id", "kind",
                                                 "reference", "exact_text", "source_uri", "source_hash"]])
    meta.create_all(engine)
    r = LegalRecord.make("L1", "syn", "v1", "article", "1", "النص التجريبي", "fixture:local")
    with engine.begin() as conn: conn.execute(t.insert(), r.__dict__)
    columns = {name: name for name in ["source_id", "instrument_id", "edition_id", "kind", "reference", "exact_text"]}
    store = SQLAlchemyStore(engine, t, lambda row: LegalRecord(**dict(row)), columns)
    assert store.get("L1") == r
    assert list(store.search(Query("النص", reference="1"), 5)) == [r]
