# NewsDOM product and technical gap baseline

Last source review: 2026-09-06

This document separates protected product truth from active candidate work. Live GitHub refs, rulesets, checks, reviews, security results, releases, and deployment evidence supersede volatile observations recorded here.

## Protected product truth

Protected `develop@e06b1f3fb10903569124af011da213951e6e2473` owns the NewsDOM bounded context: authenticated PDF intake, bounded upload handling, structural PDF admission, MinerU-backed parsing, canonical `ParseResponse`/page/article/media schemas, readiness/liveness, and document-oriented command-line utilities. `ArticleNode` naming is retained for schema stability while its ubiquitous language is a generic document section rather than a newspaper-specific article.

NewsDOM owns parsed-document truth. It does not own identity, LLM routing, ontology publication, outbound-policy authority, hostile-workload isolation, or downstream analytical decisions. Those capabilities must remain behind released/versioned owner contracts where consumed.

## Active candidate: canonical JSONL projection

PR #815 adds a local export adapter from canonical NewsDOM JSON to one JSON object per section/article line. The candidate is not protected or released truth until normal integration.

The application boundary is:

```text
NewsDOM JSON file
    -> ParseResponse validation
    -> page/article projection
    -> staged JSONL file in destination directory
    -> atomic replace of destination
```

The projection contains only `document_id`, `page_number`, `article_id`, `headline`, and ordered `body_blocks`. It does not serialize images, bounding boxes, captions, footnotes, parser quality, credentials, or authorization evidence.

### Invariants

- Input must be an existing `.json` file and must validate as the canonical `ParseResponse`; malformed nested pages/articles are rejected rather than silently discarded.
- Input and output paths must be distinct after path resolution so export cannot overwrite its source document.
- Output is built in a same-directory temporary file and replaced only after serialization completes; an exception before replacement must not publish a partial destination.
- UTF-8 and non-ASCII document text are preserved with JSON `ensure_ascii=False` semantics.
- Output order follows canonical page order and article order without inventing sorting or identifiers.

## DDD / context map

`Parser` remains the core NewsDOM domain boundary. `Document Export` is an application/adapter concern over `ParseResponse`; it does not become a second document model. The canonical schema is the anti-corruption boundary between parser output and local export tools. Downstream consumers receive a projection and must not infer omitted parser evidence or authorization from it.

## Commercial gaps after #815

The JSONL projection still has no separately versioned external schema/profile identifier. A consumer that needs a durable cross-product contract therefore cannot safely treat the current five-field shape as an immutable released API merely because the local CLI exists.

Large-document export currently validates the complete JSON document in memory before streaming JSONL records. Before claiming large-corpus throughput or a buyer-path p95 target, measure representative/right-cleared NewsDOM documents under the supported Python/runtime/storage configuration and profile parse, validation, serialization, allocation, and filesystem costs. Do not substitute reduced samples or unit-test timing for that evidence.

The staged-file replace narrows partial-publication risk but is not a complete crash-durability guarantee. If JSONL becomes a durable operational artifact, specify destination-filesystem assumptions, parent-directory durability, receipt/hash provenance, recovery behavior, and overwrite/version-retention policy.

The projection can contain document text and therefore may contain personal or confidential information present in the source. Product use that exports regulated data needs purpose-bound access, retention/disposition, audit evidence, and any required anonymization at the owning boundary; this CLI alone does not establish those controls.

## Acceptance and next actions

For #815, require deterministic schema-rejection and source-preservation regressions, exact-head repository/security/static-analysis checks, and qualifying current-head review before normal merge. Do not transfer predecessor checks after a head change.

After integration, the next buyer-facing decision is whether JSONL is only a local convenience format or a versioned interoperability contract. If it becomes a contract, define the profile/version, compatibility rules, canonical fixture corpus, provenance/receipt fields, and released documentation before another repository consumes it as authority.

No immutable NewsDOM release, deployment, performance claim, certification, or downstream interoperability guarantee is asserted by this baseline.
