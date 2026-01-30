## 2026-01-29: Session Summary: Simples Database MVP Planning and Bootstrap

### What We Accomplished

1. MVP spec work progressed from v1.0.0 → v1.0.3:

* v1.0.1: normalization updated to convert iota subscript to inline iota; references refactored to `editions` + `entry_refs`; suggestions moved to `suggested_lemmata_review` as single source of truth.
* v1.0.2: fixed Unicode escape and tightened reference/index constraints (default-edition uniqueness; composite index on refs).
* v1.0.3: removed redundancy in property assertions by introducing `property_terms` as the single source of truth and referencing it from `property_assertions`.

2. Repo bootstrap completed locally:

* Created and committed a scaffold repo named `simples` with `app/`, `supabase/`, `scripts/`, and `data-workbench/`.
* Added initial migration `supabase/migrations/001_init.sql` implementing the core tables and normalization.
* Added minimal Next.js pages for browsing lemmata and viewing lemma-linked entries.

### Major Architectural Decisions

| Decision                                   | Rationale                                                                                                                      |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Chapter-level entries, multi-lemma tagging | Compound chapters require tagging all substantively discussed lemmata; `entry_lemmata.is_primary` supports clean UI ordering.  |
| Separate lemmata for wormwood complex      | ἀψίνθιον/σέριφον/σαντόνικον remain distinct; relate via `group_member`/`distinguished_from`.                                   |
| References as first-class rows             | `editions` + `entry_refs` supports multiple editions and reference types without baking edition pages into `entries`.          |
| Suggestions single-source-of-truth         | Pending matches live only in `suggested_lemmata_review`; accepted links live only in `entry_lemmata`.                          |
| Iota subscript → inline iota               | Normalization converts U+0345 to `ι` before diacritic stripping to improve search matching (ᾠδή → ωιδη).                       |
| Properties non-redundant                   | `property_terms` stores canonical term/category/tag; `property_assertions` stores evidence + FK, avoiding repeated JSON blobs. |
| CSVs as authoritative source               | Version-controlled CSVs remain the source of truth; Supabase is the query/edit layer.                                          |
| URNs as canonical identifiers              | Stable URNs for citability and resolvable references.                                                                          |

### Data Model Highlights (current direction)

Core: `works`, `entries`, `lemmata`, `entry_lemmata` (primary/discussed)
References: `editions`, `entry_refs` (incl. “one default edition per work”)
Review: `suggested_lemmata_review`
Editor: `translation_versions`, `entry_notes`
Properties: `property_terms`, `property_assertions`
Relations (planned): `lemma_relations` (+ enum)

### Implementation Progress

* Git repo created at `~/Projects/simples/`
* First commit: “scaffold”
* Local Supabase not yet running (Supabase CLI not installed; prior curl installer URL returned 404)
* Decision: use Supabase CLI via `npx supabase ...` and Docker Desktop with Linux containers + WSL integration (no Windows containers)

### Outstanding Items

1. Install/run local Supabase tooling:

* Ensure Docker works in WSL (`docker ps`)
* Run CLI via `npx supabase start` in `supabase/`

2. Make import pipeline real (not stub):

* Confirm canonical CSV headers from the old repo
* Implement idempotent upserts in dependency order
* Add validation checks (primary lemma uniqueness, ref de-dup, etc.)

3. Feed a minimal dataset to test the UI:

* Import a small slice (few works, few lemmata, ~50 entries)

### Next Steps

1. Get Docker + local Supabase running (WSL integration, Linux containers)
2. Apply migrations (`npx supabase db reset`)
3. Implement `scripts/import_supabase.py` against your existing CSV formats
4. Run the app and confirm `/lemmata` renders imported rows
5. Only then expand editor features and suggestion review UI
