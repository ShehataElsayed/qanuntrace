"""Sketch only; point `engine` and `table` at an authorized read-only database."""
from qanuntrace import LegalRecord
from qanuntrace.adapters import SQLAlchemyStore

def make_store(engine, table):
    mapping = {key: key for key in ("source_id", "instrument_id", "edition_id", "kind",
                                  "reference", "exact_text")}
    return SQLAlchemyStore(engine, table, lambda row: LegalRecord(**dict(row)), mapping)
