# docs/work_tree.md

Version: 0.2  
Owner: Simples repo  
Scope: TEI-first text indexing, SQL-first editorial layer, cookbook integration surface, and AI-assisted development workflow with quality gates.

This work tree is structured so each leaf item can become a GitHub issue. IDs are stable. “Acceptance criteria” are written as testable outcomes.

---

## Milestones

M0 Repo workflow ready
- Agents and workflow docs in place
- Minimal CI sanity gate in place or explicitly deferred without breaking repo

M1 TEI projection layer ready
- Supabase schema supports TEI provenance, entry refs, tokens, staleness flags
- Deterministic TEI indexer can populate entries/refs/tokens

M2 Editorial workflow ready
- Translation versions and lemma linking operate on TEI-derived entry IDs
- Parallel lemma view works on real data

M3 Anchored annotation ready
- Token-span annotations stored with TEI segment hash
- Re-index marks anchors stale when TEI changes

M4 Cookbook integration surface ready
- Stable lemma IDs + lemma aliases
- Versioned lemma package export with schema validation

---

## WP00 Development workflow and quality gates

### WT-0001 Add CLI AI best practices guide
- Deliverable: `docs/cli_ai_best_practices.md`
- Acceptance criteria
  - Covers TDD, adversarial testing, sub-agent workflow, quality gating
  - Includes a short references section with credible links
  - Includes templates and stop-the-line rules

### WT-0002 Add repo agent rules
- Deliverable: `agents.md`
- Acceptance criteria
  - Defines required gates before merge
  - Defines agent roles and handoff expectations
  - Defines stop-the-line criteria

### WT-0003 Add repo workflow
- Deliverable: `Workflow.md`
- Acceptance criteria
  - Contains task brief template and DoD checklist
  - Defines fast PR gates and nightly gates
  - Defines adversarial pass guidance

### WT-0004 Add minimal CI skeleton or document deferral
- Deliverable: either `.github/workflows/ci.yml` or `docs/runbooks/ci.md`
- Acceptance criteria
  - If CI added: it does not break repo, and runs at least a minimal smoke gate
  - If CI deferred: doc states exact reason and the intended future gate set

Dependencies: none  
Milestone: M0

---

## WP0 Product spec and contracts

### WT-0101 Revise PRD to TEI-first text and SQL-first everything else
- Deliverable: `docs/prd/PRD_vNext_TEI_first.md`
- Acceptance criteria
  - Explicit authority split: TEI owns base text and citations; SQL owns editorial/relational
  - Explicit non-goals: no TEI editing in app, no `<w>` tokenization requirement
  - Phased plan matches this work tree

Dependencies: WT-0001..WT-0003 recommended  
Milestone: M0

### WT-0102 Write TEI indexing contract
- Deliverable: `docs/contracts/tei_indexing_contract.md`
- Acceptance criteria
  - Defines segment selection rules and required `xml:id`
  - Defines reading text extraction and ignored elements
  - Defines hashing, upsert semantics, and staleness behavior

Dependencies: WT-0101  
Milestone: M0

### WT-0103 Write cookbook integration contract
- Deliverable: `docs/contracts/cookbook_integration_contract.md`
- Acceptance criteria
  - States lemma ID stability rules
  - States alias/variant policy and normalization versioning
  - States export schema versioning policy

Dependencies: WT-0101  
Milestone: M0

### WT-0104 Write recipe TEI profile for CTS-safe chunking
- Deliverable: `docs/contracts/recipe_tei_profile.md`
- Acceptance criteria
  - Steps encoded as `<list type="steps"><item xml:id=…>`
  - Variant/recipe membership encoded in `<standOff>` without structural overlap
  - Linter rules defined for missing IDs and broken targets

Dependencies: WT-0101  
Milestone: M0

---

## WP1 Supabase schema changes

### WT-0201 Add TEI provenance tables
- Deliverable: migration `supabase/migrations/0xx_add_tei_docs.sql`
- Acceptance criteria
  - `tei_docs` exists with `tei_doc_id`, `source_path`, `tei_version_hash`, timestamps
  - Migration applies cleanly to a fresh local DB reset

Dependencies: WT-0102  
Milestone: M1

### WT-0202 Add TEI provenance fields to entries and enforce constraints
- Deliverable: migration `0xx_update_entries_for_tei.sql`
- Acceptance criteria
  - Entries have `tei_doc_id`, `tei_segment_id`, `tei_segment_hash`, `ordering_key`
  - Greek cache fields exist and are documented as derived
  - Unique constraint exists on `(tei_doc_id, tei_segment_id)`
  - No application code changes required to apply migration

Dependencies: WT-0201  
Milestone: M1

### WT-0203 Add entry refs table
- Deliverable: migration `0xx_add_entry_refs.sql`
- Acceptance criteria
  - `entry_refs` exists and supports structure and edition refs
  - Indexes support lookup by `entry_id`

Dependencies: WT-0202  
Milestone: M1

### WT-0204 Add tokens table
- Deliverable: migration `0xx_add_tokens.sql`
- Acceptance criteria
  - Tokens keyed by `(entry_id, tei_segment_hash, token_idx)` or equivalent
  - Fields include form, normalized, offsets, token_type
  - Indexes support querying tokens by entry and hash

Dependencies: WT-0202  
Milestone: M1

### WT-0205 Add staleness metadata to annotations and assertions
- Deliverable: migration `0xx_add_staleness.sql`
- Acceptance criteria
  - Annotations and assertions include `tei_segment_hash` and `stale` flag
  - Existing rows remain valid with safe defaults

Dependencies: WT-0204  
Milestone: M1

### WT-0206 Add lemma aliases table
- Deliverable: migration `0xx_add_lemma_aliases.sql`
- Acceptance criteria
  - `lemma_aliases` exists with alias text, normalized alias, alias_type
  - Unique constraint prevents duplicate aliases per lemma/type
  - Index exists on `alias_normalized`

Dependencies: WT-0103  
Milestone: M4

### WT-0207 Add import runs table
- Deliverable: migration `0xx_add_import_runs.sql`
- Acceptance criteria
  - `import_runs` table exists with run status and report JSON
  - Indexer can write a run summary

Dependencies: WT-0201  
Milestone: M1

---

## WP2 Shared normalization and tokenization library

### WT-0301 Create shared textutils package
- Deliverable: `packages/textutils/`
- Acceptance criteria
  - Exposes `NORMALIZATION_VERSION` and `TOKENIZER_VERSION`
  - Includes Greek normalization function used by scripts
  - Includes deterministic tokenizer returning offsets and normalized forms
  - Unit tests cover determinism

Dependencies: WT-0102  
Milestone: M1

### WT-0302 Align app normalization with shared spec
- Deliverable: either code change or doc note in `docs/contracts/`
- Acceptance criteria
  - Single documented normalization policy for search and matching
  - If app keeps TS normalization: it matches spec or is clearly labeled “UI-only”

Dependencies: WT-0301  
Milestone: M2

---

## WP3 TEI validation and indexing pipeline

### WT-0401 Add per-doc TEI indexing config format
- Deliverable: `config/tei_docs/*.yml` plus `config/tei_docs/README.md`
- Acceptance criteria
  - Config supports: tei_doc_id, source_path, segment selector, ignore rules, milestone rules
  - At least one concrete config exists for a real TEI file

Dependencies: WT-0102  
Milestone: M1

### WT-0402 Implement TEI validator
- Deliverable: `scripts/validate_tei.py`
- Acceptance criteria
  - Hard errors on missing/duplicate `xml:id` in selected segments
  - Warns on missing milestones and empty extracted text
  - CLI supports `--config` and exits non-zero on hard errors

Dependencies: WT-0401  
Milestone: M1

### WT-0403 Implement deterministic TEI indexer with dry-run
- Deliverable: `scripts/index_tei.py`
- Acceptance criteria
  - Computes tei_version_hash and per-segment tei_segment_hash
  - Upserts `tei_docs` and `entries`, replaces `entry_refs` and `tokens`
  - Ignores `note[@type="footnote"]` in reading stream
  - `--dry-run` produces a stable report without DB writes

Dependencies: WT-0201..WT-0207, WT-0301, WT-0401  
Milestone: M1

### WT-0404 Implement deletion and deprecation handling
- Deliverable: enhancement to `scripts/index_tei.py`
- Acceptance criteria
  - Segments not present in the new run are marked `deprecated=true`
  - No destructive deletes by default

Dependencies: WT-0403  
Milestone: M1

### WT-0405 Implement staleness marking on hash change
- Deliverable: enhancement to `scripts/index_tei.py`
- Acceptance criteria
  - If entry’s `tei_segment_hash` changes, existing annotations/assertions targeting old hash are flagged stale
  - Stale items remain readable and queryable

Dependencies: WT-0403, WT-0205  
Milestone: M3

### WT-0406 Implement index-output validator
- Deliverable: `scripts/validate_index_output.py`
- Acceptance criteria
  - Verifies determinism on same input in dry-run mode
  - Verifies required DB invariants after a real run
  - Produces a concise report

Dependencies: WT-0403  
Milestone: M1

---

## WP4 Versioned exports for cookbook integration

### WT-0501 Define lemma package JSON schema
- Deliverable: `schemas/exports/lemma_package.v1.schema.json`
- Acceptance criteria
  - Schema validates required fields and version metadata
  - Schema supports lemmata list and alias list with alias_type

Dependencies: WT-0103, WT-0206, WT-0301  
Milestone: M4

### WT-0502 Implement lemma package exporter
- Deliverable: `scripts/export_lemma_package.py`
- Acceptance criteria
  - Writes `data/releases/lemma_package/<version>/lemma_package.json`
  - Writes sha256 and manifest including normalization/tokenizer versions
  - Output validates against schema

Dependencies: WT-0501  
Milestone: M4

### WT-0503 Implement entry lemma links exporter
- Deliverable: `scripts/export_entry_lemma_links.py`
- Acceptance criteria
  - Exports mapping entry_id → lemma_id(s) with relation_type
  - Output includes export_version and content hash

Dependencies: WT-0502 recommended  
Milestone: M4

---

## WP5 Tests and CI gates

### WT-0601 Add unit tests for textutils determinism
- Deliverable: tests under `packages/textutils/tests/`
- Acceptance criteria
  - Tokenization is deterministic across runs
  - Normalization is deterministic and documented

Dependencies: WT-0301  
Milestone: M1

### WT-0602 Add indexer determinism test fixture
- Deliverable: `tests/fixtures/tei/` plus test file
- Acceptance criteria
  - Same TEI fixture indexed twice yields identical hashes and token outputs in dry-run

Dependencies: WT-0403  
Milestone: M1

### WT-0603 Add drift and staleness regression test
- Deliverable: test that modifies a fixture segment and re-indexes
- Acceptance criteria
  - Segment hash changes detected
  - Stale flags are set on anchored objects

Dependencies: WT-0405  
Milestone: M3

### WT-0604 Add export schema validation test
- Deliverable: test validating lemma_package output against JSON schema
- Acceptance criteria
  - Export passes schema validation
  - Schema failure yields useful error output

Dependencies: WT-0502  
Milestone: M4

### WT-0605 Add CI gate profile
- Deliverable: `.github/workflows/ci.yml` or documented deferral
- Acceptance criteria
  - Runs unit tests and validators in a bounded time
  - Includes at least TEI validation dry-run on one configured doc or fixture

Dependencies: WT-0004, WT-0402, WT-0602  
Milestone: M0 and M1

---

## WP6 App integration for TEI-derived entries

This WP is scoped to minimal changes needed so the app can browse TEI-indexed entries without treating Greek as editable.

### WT-0701 Update data access to use TEI-derived entry IDs
- Deliverable: app query updates in `app/src/`
- Acceptance criteria
  - Lemma pages still resolve linked entries
  - Entries show citations from entry_refs where present

Dependencies: WT-0403  
Milestone: M2

### WT-0702 Translation editor uses SQL-owned versions
- Deliverable: translation UI and API hooks
- Acceptance criteria
  - Editing translation never touches Greek cache fields
  - Version history visible per entry

Dependencies: WT-0701  
Milestone: M2

### WT-0703 Parallel lemma viewer works on TEI-indexed data
- Deliverable: new route or enhancement to existing lemma pages
- Acceptance criteria
  - For lemma_id, show all linked entries with citations and translations

Dependencies: WT-0701  
Milestone: M2

---

## WP7 Token-span annotations

### WT-0801 Add token-span selection and storage
- Deliverable: UI and DB writes for annotations with (start_token_idx, end_token_idx)
- Acceptance criteria
  - User can create an annotation anchored to token spans
  - Annotation renders with highlighted quote

Dependencies: WT-0403, WT-0204, WT-0701  
Milestone: M3

### WT-0802 Stale annotation review UI
- Deliverable: UI path for stale=true annotations
- Acceptance criteria
  - Stale annotations are discoverable
  - User can mark reviewed or re-anchor

Dependencies: WT-0405, WT-0801  
Milestone: M3

---

## WP8 Derived overlays and enrichment

These are explicitly phase-gated and may live as scripts and derived tables first.

### WT-0901 Glossary and co-mention extraction
- Deliverable: script or query producing co-mentioned terms per lemma
- Acceptance criteria
  - Output keyed by lemma_id and entry_id, reproducible from tokens
  - Can be stored as derived table or export artifact

Dependencies: WT-0403, WT-0204  
Milestone: post-M3

### WT-0902 NER suggestions pipeline
- Deliverable: offline script generating entity suggestions with evidence spans
- Acceptance criteria
  - Suggestions are non-destructive and reviewable
  - Evidence spans link back to entry_id and token indices

Dependencies: WT-0403, WT-0801 recommended  
Milestone: post-M3

### WT-0903 Property assertions workflow
- Deliverable: assertion UI or script to attach structured properties with evidence spans
- Acceptance criteria
  - Assertions queryable by lemma_id and type
  - Evidence spans preserved and staleness supported

Dependencies: WT-0405, WT-0801  
Milestone: post-M3

---

## Issue template for leaf tasks

Title: WT-XXXX Short imperative title  
Goal: one sentence  
Scope: bullet list  
Non-goals: bullet list  
Acceptance criteria: bullet list  
Dependencies: list WT-IDs  
Validation: commands to run locally  
Rollback: how to revert safely

---

## Dependency notes

- WP1 and WP2 are prerequisites for WP3.
- WP3 must land before WP6 and WP7.
- Cookbook integration surface is WP4 plus lemma_aliases in WP1.
- Recipe TEI profile affects cookbook TEI authoring, not the Simples indexer unless enabled; keep overlays ignored by default.
