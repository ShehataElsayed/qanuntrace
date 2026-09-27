# Integration guide for the database team

## 1. Map the local schema

Minimum fields for `LegalRecord`:

| Field | Meaning |
| --- | --- |
| `source_id` | Stable, unique per stored source record; never recycle. |
| `instrument_id` | Stable ID for the specific law or regulation, never just a title. For judgments, court/source family. |
| `edition_id` | Source edition/version, not merely ingestion time. |
| `kind` | `article`, `regulation` or `judgment`. |
| `reference` | Exact article/paragraph or judgment identifier as published. |
| `exact_text` | Unmodified original Unicode text after an explicitly documented acquisition process. |
| `source_hash` | SHA-256 of UTF-8 encoded `exact_text` at ingestion. |
| `source_uri` | Source identifier or internal pointer; do not invent an official URL. |
| `effective_from`, `effective_to` | ISO dates, inclusive/exclusive; NULL means unknown, not currently effective. |
| `court`, `judgment_status`, `paragraph` | Metadata, NULL when unknown; never infer finality. |
| `access_label` | Optional tenant/authorization label checked on reads. |

Make `source_id` unique, and index (`instrument_id`, `edition_id`, `reference`, `kind`). Add typed relations for amendment/supersession and judgment-to-article citations with source spans and reviewer identity. Separate cases with restricted content from public sources. Keep an original document or auditable copy, source retrieval time, OCR confidence where relevant, publication date, original instrument number, Hijri and Gregorian dates with conversion provenance, effective/repeal/transition dates, court, docket, decision number, judgment date, status and redaction provenance where available. These extra fields are not yet part of the core typed record; preserve them in your DB mapping/sidecar instead of discarding them.

## 2. Provide a read-only adapter

Implement `get(source_id) -> LegalRecord | None` and `search(query, limit) -> Iterable[LegalRecord]`. `search` MUST enforce tenant ACL before returning source text. `get` MUST enforce the same ACL in your application context: the sample protocol alone cannot carry a user principal. The app should use a tenant-bound adapter instance and server-side authorization for each query. Do not connect with a write-capable account. SQL examples in `examples/sql_mapping.py`; for NoSQL, make your own adapter with the same methods.

The included SQL adapter makes a generic portable SELECT with parameter binding. Its `reference` equality expects DB-side canonicalization or custom matching for numeral variants. Its LIKE search is a development baseline and may be slow; add your own full-text index/reranker. Search and vector adapters may use approximate recall, but hydrate exact text through the authoritative database and verify hashes. External search indexes must not be treated as source-of-truth text.

## 3. Wire a model

Implement `propose(query, records) -> Iterable[EvidenceProposal]`, or use one of the included optional SDK wrappers. It must return only candidate quotes with offsets. If the model returns a legal inference, put it in `interpretation` so it is withheld for human review. Any relation stronger than a mere mention requires review. Never present a generated passage as statutory text. Set provider keys through your secure deployment environment, not a config or chat attachment. Use local models when case-data residency requires it.

## 4. Integration and acceptance

Build a gold set with Saudi-law professionals: versions/amendments, repealed and not-yet-effective provisions, identical article numbers across systems, nested paragraphs, Arabic/Indic/Western digits, ambiguous questions, date conversion, conflicting and non-final judgments, merely cited vs applied provisions, OCR errors, false citations and unanswerable requests. Measure article/version accuracy, quote exact-match, judgment-relation precision, hallucination/unsupported-sentence rate, abstention rate and p95 latency on your environment. Verify that all data and license rights permit your chosen use. Review remote-provider data transfer and tenant isolation. Run security review, rate limits, observability, disaster recovery and rollback before production.

**Release gate:** changing code or adding a DB/model adapter does not imply legal validation. No official Saudi corpus is bundled; publisher terms and data licenses must be checked separately. Outputs should state their source edition and review status, and users should verify consequential legal decisions with qualified counsel.

## Config-only setup for SQL and JSONL

See `examples/config/{sqlite,postgres,jsonl}.json`. Set `QANUNTRACE_DATABASE_URL` to a read-only SQLAlchemy URL in your deployment secret manager, e.g. `sqlite+pysqlite:///...` or `postgresql+psycopg://...` (install the matching database driver). Change JSON column names to match your existing table. Run `qanuntrace-doctor examples/config/sqlite.json`; a zero exit code means one sample row's fields and hash were read, not that the whole corpus is correct. For Elasticsearch/OpenSearch, vector and NoSQL deployments, configure the client in the host service and implement or use the corresponding adapter; these cannot be wired blindly from an unknown schema with a universal JSON file.

## Other config-driven stores

`examples/config/mongodb.json` uses a MongoDB text index (`$text`) and `QANUNTRACE_MONGO_URL`; `elasticsearch.json` and `opensearch.json` use their standard clients, a named index and `QANUNTRACE_SEARCH_URL`. Exact source fields must be mapped, and local ACL enforcement remains the team's responsibility. Their indices must be configured by your team; `doctor` only checks that a sample record can be read.

`examples/config/qdrant.json` uses Qdrant vector IDs and hydrates exact records from the configured authoritative SQL store. Set `QANUNTRACE_QDRANT_URL` and optionally `QANUNTRACE_QDRANT_API_KEY`. Vector search requires a matching embedding function, loaded from your application module named in `embedding_callable`; that function must be supplied and versioned by the team because no universal embedding matches every vector index. For pgvector, use the standard PostgreSQL SQLAlchemy backend with your own preexisting pgvector search query or a custom `LegalStore`. There is no safe universal similarity metric/index configuration to infer. No connector can guess a proprietary schema, index, tenant policy or provider-specific auth settings.

## Security and source architecture (v0.2.0)

```text
Authorized app principal -> DB/RLS -> LegalStore.get/search -> hydrated source IDs
                                  |-> lexical + vector indices (IDs only)
                                  |-> version intervals + BOE secondary links
                                  -> exact quote + optional trusted upstream signature
                                  -> human review -> permitted redacted model transfer
```

The source DB must enforce tenant ACL/RLS before any text reaches indexes, caches, logs or models. Use a tenant-bound adapter and a pinned upstream public key if signed provenance is available. BOE links are secondary and never prove currency; Gazette ingestion requires a separately licensed/approved source. Najiz API access requires the deploying organization to register and obtain a specific service grant. A configured `approved_get` endpoint alone is not a grant; deployers must supply an approved endpoint, bounded client, data rights and schema tests. No API keys belong in the repository. Keep redaction maps local, encrypted and access-controlled if the application adds reversible pseudonyms. Do not automatically restore original identities to model output.

## Local and API model adapters

Provide a `TextModel.complete(system, user)` method, or wrap a callable in `FunctionModel`. The callable can invoke a local Ollama/vLLM/Transformers runtime or an API SDK, but model names, token limits, output shape, auth and residency depend on the deployed version. `ProposalBridge` requires an `approve_transfer(query, records)` callback and bounds the total context; it does not itself redact records. Pair a remote model with a reviewed redaction policy, use only sources the principal can access, parse proposals as JSON, and pass them to `Pipeline` for exact-span verification. Test each chosen provider and model release using the labeled legal cases; do not infer compatibility from a protocol alone.
