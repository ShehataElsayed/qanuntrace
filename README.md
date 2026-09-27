# QanunTrace

A provider-neutral, database-neutral legal evidence pipeline. This package contains code and synthetic test fixtures only. It does not include Saudi legal texts, judgments, a crawler, or a database connection to your systems.

**Status:** integration candidate, not production-certified. Exact quotations are programmatically checked against the text supplied by your database, but relevance, completeness, currency, statutory interpretation and the legal effect of judgments are not guaranteed. This is not legal advice. A deployer must perform legal review and integration testing before relying on it.

## Quick start

```bash
python -m pip install -e '.[dev,sql]'
pytest -q
```

`examples/local_demo.py` shows a synthetic in-memory source. Run `python examples/local_demo.py` after installing. The team-facing integration guide is in `docs/INTEGRATION.md` and `docs/INTEGRATION_AR.md`.

## Pipeline

1. The caller supplies a `Query` with scope (instrument, article, kind and effective date if known).
2. A `LegalStore` retrieves candidate records. A lexical reranker is supplied as a baseline. Deployers may replace ranking and add a vector search that hydrates from the authoritative store.
3. The model proposes structured evidence spans. It does not write the answer directly.
4. `verify` checks record membership, source hash, identity, article number, selected date, access label and exact quote span. Judgment-article relations and interpretive assertions are withheld for review.
5. The answer formatter emits only verified quotations. Everything else is excluded or triggers abstention. Each stage has an audit event with non-sensitive codes and counts.

The source hash catches accidental differences against the hash stored with the record. It is not a cryptographic attestation of the upstream publisher. The store itself and its ingestion process must be trusted. Character offsets are Python Unicode codepoint offsets, not byte offsets. The stored UTF-8 hash checks whole-record bytes; future versions should keep raw bytes and byte-offset maps for a stronger byte-for-byte proof.

## Adapters

- `MemoryStore` / `JSONLStore`: fixtures and small local snapshots.
- `SQLAlchemyStore`: caller-defined column mapping for SQLite, PostgreSQL and other SQLAlchemy engines. Uses portable LIKE, not optimized full-text search.
- `SearchStore`: Elasticsearch/OpenSearch compatible client (read-only). Different client versions and mappings need team tests.
- `VectorStore` / `chroma_store`: vectors return IDs only, then exact text is hydrated from the authoritative store.
- `CallableGenerator`, `OpenAICompatibleGenerator`, `AnthropicGenerator`, `GoogleGenerator`: optional SDK clients. Credentials are supplied by the deployer. Remote models may receive full retrieved snippets, so configure privacy controls before use.

A backend or model not listed can implement the two short protocols. "All database/model types" means the interface can adapt them, not that every version is certified out of the box.

## Known limits and gates

- Legal relevance and entailment are not validated by a quotation hash. Interpretive claims and judgment relations remain review-only. No automatic claim of zero hallucination.
- No automatic amendment watcher, official-feed integration, Saudi-source license grant, legal-text redistribution, scanned-PDF OCR validation or controlled-production deployment.
- Need the team's real schema, source/version policy, ACL and data rights; a redacted benchmark of ambiguous questions, amendments and judgments; latency/security acceptance thresholds; and provider compatibility tests.
- Do not feed privileged or personal case data to third-party APIs without authorization, DPA/privacy review and appropriate redaction.

Copyright 2026 Shehata El-sayed. Licensed under Apache-2.0; see LICENSE. Legal source data carries separate rights.

## Source and distribution

The package name is QanunTrace. The repository includes Python source, tests, examples and docs; release artifacts include the wheel and source distribution. Version 0.1.0 identifies the integration candidate, not a certified legal version. The Apache-2.0 license applies to original code only; legal-source data carries separate rights.

## Configuration without editing code

For a SQL table with the documented fields, copy `examples/config/sqlite.json` or `postgres.json`, map your column names, set `QANUNTRACE_DATABASE_URL` in your environment, then run `qanuntrace-doctor your-config.json`. The doctor performs a read-only sample query and hash check. For JSONL use its example config. Search engine, vector and NoSQL connectors need a configured client or a custom adapter in the embedding application; they are not zero-code connectors. A team cannot safely integrate an unknown schema or judgment ontology by config alone without validation.
