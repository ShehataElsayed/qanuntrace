# QanunTrace

A provider-neutral, database-neutral legal evidence pipeline. This package contains code and synthetic test fixtures only. It does not include Saudi legal texts, judgments, a crawler, or a database connection to your systems.

**Scope and assurance:** QanunTrace checks exact quotations against records supplied by a deployment. Source currency, completeness, relevance, statutory interpretation and judgment effect require qualified legal review and integration testing. It is not legal advice or a certified compliance system.

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

The package name is QanunTrace. The repository includes Python source, tests, examples and docs; release artifacts include the wheel and source distribution. Version 0.2.0 adds guarded integration building blocks; no release version is a certification of legal conclusions or a particular deployment. The Apache-2.0 license applies to original code only; legal-source data carries separate rights.

## Configuration without editing code

For a SQL table with the documented fields, copy `examples/config/sqlite.json` or `postgres.json`, map your column names, set `QANUNTRACE_DATABASE_URL` in your environment, then run `qanuntrace-doctor your-config.json`. The doctor performs a read-only sample query and hash check. For JSONL use its example config. Search engine, vector and NoSQL connectors need a configured client or a custom adapter in the embedding application; they are not zero-code connectors. A team cannot safely integrate an unknown schema or judgment ontology by config alone without validation.

## Legal structure and evaluation modules

`legal.article_mentions` identifies numeric article mentions in Arabic text, while `link_candidates` returns review-only links to matching-number articles. `edition_diff` reports textual edits between two verified records of the same article. None infers legal effect or resolves competing laws. `evaluation.evaluate` computes source/quote/abstention rates on a professionally reviewed gold set; `review.review_queue` exports withheld proposed interpretations. Written-out article ordinals and complex Arabic morphology are not fully parsed.

## Persistent review memory

`SQLiteReviewMemory` stores reviewer annotations with tenant, reviewer, time and source hash. When the source hash changes it refuses to return the old annotation as current. `forget` deletes an entry. `EphemeralCache` is bounded and keys entries by tenant/source/hash/query. These are notes and performance aids, **never authority for a legal answer**; the pipeline always returns to the authoritative database for quotation. This is a basic reference backend, not a "giant" scalable memory system: Postgres/Redis/distributed tenancy, retention, encryption, audit access and erasure operations require deployment-specific engineering and review.

## Evidence graph

`EvidenceGraph` stores typed relations between source IDs with exact supporting spans and a reviewer identity for substantive links. It can expand reviewed neighbors up to bounded hops/nodes, re-reading the source for each edge. This is a reference in-process graph; it does not yet persist to Neo4j/Postgres or discover legal concepts automatically. A same-number article candidate is never automatically an `applies` relation.

## Professional review modes

`reasoning.make_review_plan` offers three structured, review-only checklists: lawyer (issues, support, adverse authority, procedure), counsel (facts, current rules, risks, alternatives) and judge (fact characterization, rule hierarchy/temporal applicability, evidence, reasons). These are not simulated legal professionals or judicial decisions. They do not apply Saudi source hierarchy automatically; every proposed application and conclusion requires an exact source span and qualified human review.

## Query understanding

`query.parse_query` preserves the original question, creates a separate search-normalized form, recognizes a small set of Arabic/English numeric and written-out article references, accepts caller-provided law-name aliases, classifies basic intent and requests clarification for ambiguous article/law scope. It does not silently choose between statutes. This is a conservative baseline, not full dialect or typo understanding; real Saudi legal queries need an annotated evaluation set and optional pluggable language analysis.

## File ingestion

`Extractor` reads UTF-8 text/Markdown/JSON/HTML/XML, CSV, PDF (`pypdf`), DOCX (`python-docx`) and XLSX (`openpyxl`). A bounded ZIP reader rejects path traversal, oversized entries and oversized expansion. Plug an OCR callback for images or a transcription callback for audio/video. Extracted text always carries a file hash and page/row/cell/paragraph/media locator, and is marked `needs_review`. Scanned-PDF OCR and video keyframes require external processing adapters; no legal text extracted from files is automatically trusted. Install `.[ingest]` for document dependencies. Excel formulas are read as cached values only.

## Arabic language and dates

`arabic.gulf_search_key` applies a conservative Saudi/Gulf colloquial lexicon to retrieval keys, not legal quotations. `number_word` recognizes digits, ordinal/cardinal units and simple compounds through 99; unsupported phrases return `None`. `parse_date` accepts Arabic/Persian/Western digit dates with explicit Hijri/Gregorian markers, and the optional `hijridate` Umm al-Qura converter. Unmarked calendar dates are rejected as ambiguous. It does not claim all Arabic dialects, full Arabic number grammar or authoritative Hijri conversion outside the library's supported range; the official source date prevails.

## Enterprise integration building blocks (v0.2.0)

The following modules are local building blocks, not deployment certification. `legal_reference.parse_legislative_reference` parses a bounded set of Arabic article, repeated-article, paragraph and item references, returning `needs_review` when an expression is outside its grammar. `privacy.redact` masks some syntactic IDs, Saudi mobile numbers and emails; it does not reliably detect names, context-dependent identifiers, financial data or OCR errors. `gateway.prepare_remote_transfer` blocks transfer until the deploying app records policy approval and reviews the redacted data. These are not automatic PDPL/GDPR compliance or an excuse to send confidential client files to a third-party model.

`temporal.version_view` compares caller-curated effective-date intervals and flags missing/overlapping versions; it cannot know whether the corpus is complete. `retrieval.HybridStore` combines lexical/vector IDs with reciprocal-rank fusion, hydrating through the authority store and requiring a principal-bound authorization predicate. The deployer must enforce ACL/RLS before either search index sees confidential text and on every `get`; `access.AuthorizedStore` is an additional deny-by-default application guard, not a substitute for database RLS. `provenance.verify_signed_source` accepts an upstream signer and pinned verifier; generating a hash ourselves would not authenticate the publisher. `metrics` reports exact-span verification rates and separately aggregates supplied human faithfulness/relevance labels, not automated legal truth. `health.health_check` returns a read-only one-record, no-private-ID JSON-compatible report.

`secondary.boe_reference` validates caller-supplied Bureau of Experts links as secondary references without fetching or redistributing text. BOE's own [FAQ](https://www.boe.gov.sa/ar/Help/FAQ/Pages/default.aspx) says its consolidations are periodic and the Gazette/National Center are the immediate official publication sources. `government.approved_get` is only a fixed-host, opt-in transport hook for an approved endpoint and a caller-supplied TLS/timeout/no-redirect client; it neither registers an account nor assumes endpoint access, licensing, rights, freshness or response schema. The [Najiz developer catalog](https://developers.najiz.sa/en/api-catalog) has case/judgment services that require service-specific registration and approval. [MOJ open-data policy](https://www.moj.gov.sa/ar/OpenData/Pages/OpenDataPolicy.aspx) supports machine-readable datasets, but no public full-text statutes/judgments API endpoint is verified for this package. The [Saudi Bar Association legal library API](https://library-api.sba.gov.sa/) was unavailable when checked. These endpoints are integration candidates, not live QanunTrace connectors.

A `CuratedOntology` accepts only reviewer-attributed search aliases. It returns candidate concept IDs and never treats "contract" and "obligation" as interchangeable legal rules. A deployer-supplied morphology analyzer may augment search terms after an annotated Arabic benchmark; no CAMeL model or weights ship here. Do not present either expansion as source text or as legal entailment.

`cache.VerifiedCache` binds values to tenant, principal scope, source ID/hash, effective interval and a query hash. It checks the authoritative current hash on every read and evicts a changed source; callers can also invalidate by source on an approved amendment event. This is an in-process reference, not a Redis deployment or a Gazette watcher. It cannot detect amendments the authoritative database has not ingested.

`model_bridge.TextModel` and `ProposalBridge` provide a small provider-agnostic interface for local/open-weight model runners or remote APIs. The deployer supplies `complete(system, user)`, an explicit transfer policy, a schema-compatible model response and a tested adapter. OpenAI-compatible SDK clients can target a local server with a configurable base URL; Anthropic and Google wrappers are available as optional transport examples. Ollama, vLLM, Transformers and custom APIs are possible via `FunctionModel`, but no claim is made that every model version has been integration-tested. The bridge bounds context size and feeds only structured proposals back to the verified pipeline. A remote provider still requires the deployment's privacy/legal data-transfer review; use `gateway.prepare_remote_transfer` or an equivalent reviewed policy before sending case data.
