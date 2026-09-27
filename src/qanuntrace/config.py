"""Configuration-only SQL/JSONL wiring. Connections are provided by env variables."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .adapters import JSONLStore, MongoStore, QdrantStore, SearchStore, SQLAlchemyStore
from .types import LegalRecord

_FIELDS = set(LegalRecord.__dataclass_fields__)
_REQUIRED = {"source_id", "instrument_id", "edition_id", "kind", "reference",
             "exact_text", "source_uri", "source_hash"}

def load_config(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("backend") not in ("sqlalchemy", "jsonl", "mongodb", "elasticsearch", "opensearch", "qdrant"):
        raise ValueError("unsupported backend in configuration")
    return value

def map_record(row: Any, fields: dict[str, str]) -> LegalRecord:
    if not _REQUIRED.issubset(fields) or set(fields) - _FIELDS:
        raise ValueError("invalid or incomplete field mapping")
    data = {target: row[source] for target, source in fields.items()}
    return LegalRecord(**data)

def make_store(config: dict[str, Any]):
    backend = config.get("backend")
    if backend == "jsonl":
        path = config["path"]
        fields: dict[str, str] = config.get("fields") or {}
        return JSONLStore(path, lambda row: map_record(row, fields)) if fields else JSONLStore(path)
    if backend == "sqlalchemy":
        from sqlalchemy import MetaData, Table, create_engine
        env = config.get("database_url_env", "QANUNTRACE_DATABASE_URL")
        url = os.environ.get(env)
        if not url:
            raise ValueError(f"missing database URL environment variable: {env}")
        fields = config["fields"]
        engine = create_engine(url)
        table = Table(config["table"], MetaData(), schema=config.get("schema"), autoload_with=engine)
        return SQLAlchemyStore(engine, table, lambda row: map_record(row, fields), fields)
    if backend == "mongodb":
        from pymongo import MongoClient
        env = config.get("database_url_env", "QANUNTRACE_MONGO_URL")
        url = os.environ.get(env)
        if not url:
            raise ValueError(f"missing MongoDB URL environment variable: {env}")
        fields = config["fields"]
        client = MongoClient(url, serverSelectionTimeoutMS=5000)
        collection = client[config["database"]][config["collection"]]
        return MongoStore(collection, lambda row: map_record(row, fields),
                          fields["source_id"], fields["instrument_id"], fields["kind"])
    if backend in ("elasticsearch", "opensearch"):
        env = config.get("database_url_env", "QANUNTRACE_SEARCH_URL")
        url = os.environ.get(env)
        if not url:
            raise ValueError(f"missing search URL environment variable: {env}")
        if backend == "elasticsearch":
            from elasticsearch import Elasticsearch
            client = Elasticsearch(url)
        else:
            from opensearchpy import OpenSearch
            client = OpenSearch(url)
        fields = config["fields"]
        return SearchStore(client, config["index"], lambda row: map_record(row, fields))
    if backend == "qdrant":
        from qdrant_client import QdrantClient

        from .generators import CallableGenerator  # noqa: F401 - provider configured separately
        env = config.get("database_url_env", "QANUNTRACE_QDRANT_URL")
        url = os.environ.get(env)
        if not url:
            raise ValueError(f"missing Qdrant URL environment variable: {env}")
        # Vector query needs an embedding model. Load it from a configured callable
        # module only when expressly enabled by the deploying team.
        from importlib import import_module
        module_name, function_name = config["embedding_callable"].split(":", 1)
        embed = getattr(import_module(module_name), function_name)
        authority = make_store(load_config(config["authority_config"]))
        client = QdrantClient(url=url, api_key=os.environ.get(config.get("api_key_env", "QANUNTRACE_QDRANT_API_KEY")))
        return QdrantStore(client, config["collection"], embed, authority)
    raise ValueError("unsupported backend")

def doctor(config: dict[str, Any]) -> list[str]:
    """Check read-only connectivity and mapping, never mutate a table."""
    store = make_store(config)
    from .types import Query
    rows = list(store.search(Query(""), 1))
    if not rows:
        return ["connected", "no_sample_row_found; verify schema manually"]
    record = rows[0]
    from hashlib import sha256
    if sha256(record.exact_text.encode("utf-8")).hexdigest() != record.source_hash:
        return ["connected", "sample_hash_mismatch"]
    return ["connected", "sample_record_valid", "source_id:" + record.source_id]
