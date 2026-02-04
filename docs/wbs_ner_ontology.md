# docs/wbs_ner_ontology.md

# NER + Empirical Ontology Workflow (TEI corpus)

This document specifies an empirical, auditable workflow for (1) open-coded mention annotation across TEI texts, (2) induction of a Minimal Viable Ontology (MVO) from evidence, (3) bootstrapping entity registries/lexicons, (4) scaling tagging across the full corpus with human review, and (5) optional TEI enrichment as an export surface (standOff-first).

Design constraints:
- Canonical truth lives in structured data (DB/JSONL), not in hand-edited inline TEI.
- Anchoring must be stable across text edits: CTS passage + token offsets, with re-anchoring support.
- Early stages are “mention logging” (empirical). Canonical entity linking comes later.

Assumptions:
- Canonical TEI inputs are in `tei/output/`.
- CTS URNs follow your house convention, e.g. `urn:cts:greekLit:tlgNNNN.tlgNNN.aos-grc1:...`
- Greek normalization matches your DB normalization function (accents stripped, casefold, iota-subscript handling, etc.). Use the same normalization implementation across scripts.

---

## Repo artifacts

Normative docs/specs:
- `docs/wbs_ner_ontology.md` (this file)
- `docs/ontology_coding_guidelines.md` (operational coding manual; evolves)
- `data/ontology/mvo.yaml` (versioned MVO; evolves)
- `data/ontology/relations.yaml` (allowed relations + constraints; evolves)

Operational data:
- `data/token_index/{workSlug}.json` (tokenization + passage→token ranges)
- `data/samples/sample_manifest.json` (stratified sampling plan)
- `data/annotations/open_coding/{annotator}.jsonl`
- `data/annotations/adjudicated/gold_v{n}.jsonl`
- `data/entities/{places,tools,processes,properties,materials}.tsv`
- `data/lexicons/{places,tools,processes,properties,materials}.tsv`
- `data/annotations/linked/{workSlug}.jsonl` (auto/reviewed)
- `reports/iaa/*`, `reports/coverage/*`, `reports/drift/*`

Agent prompts:
- `prompts/agents/*.md` (one role per file)

Scripts (skeletons; deterministic I/O):
- `scripts/build_token_index.py`
- `scripts/make_sample_manifest.py`
- `scripts/compute_iaa.py`
- `scripts/make_adjudication_queue.py`
- `scripts/build_gold_from_open_coding.py`
- `scripts/bootstrap_entities_from_gold.py`
- `scripts/build_lexicons.py`
- `scripts/link_mentions.py`
- `scripts/tag_with_lexicons.py`
- `scripts/make_review_queue.py`
- `scripts/reanchor_spans.py`
- `scripts/export_tei_with_standoff.py`

---

## Data model: mention annotations (JSONL)

One line = one mention span.

Required fields:
- `work_urn`: CTS base URN (string)
- `passage_urn`: CTS passage URN (string)
- `work_slug`: stable work identifier used in paths (string)
- `token_start`: int (inclusive)
- `token_end`: int (exclusive)
- `surface`: exact surface form (string)
- `surface_norm`: normalized surface form (string)
- `provisional_type`: from the Provisional Coding Set (string)
- `certainty`: one of `low|med|high` (or numeric 0–1 if you prefer)
- `annotator_id`: string
- `timestamp`: ISO string

Optional fields:
- `mention_id`: stable span identifier string (recommended; enables relations to target a mention)
- `provisional_subtype`: string (free text early)
- `relations`: list of relation objects (see below)
- `notes`: string
- `evidence_window`: list of tokens (or a short snippet) for re-anchoring

Relation object (optional; used sparingly in open coding):
- `rel`: string (must exist in `data/ontology/relations.yaml`)
- `target`: string (target mention span id OR target entity id if already linked)
- `certainty`: `low|med|high`

---

## Provisional Coding Set (Phase 1 only)

These are coding buckets, not the final ontology:
- `PLACE`
- `INSTRUMENT`
- `ACTION`
- `QUALITY`
- `MATERIAL`
- `MEASURE`
- `PERSON_GROUP` (rare)

Rule: Phase 1 agents MUST NOT invent new types. Disagreements get adjudicated and can motivate splits later.

---

## Phases (WBS-style)

### Phase 0 — Scaffolding and determinism
Goal: make every later step reproducible.

Tasks:
0.1 Implement tokenization + normalization used everywhere.
0.2 Build per-work token index from TEI.
0.3 Build stratified sample manifest for empirical coding.

Deliverables:
- `data/token_index/*.json`
- `data/samples/sample_manifest.json`

Acceptance criteria:
- Token index deterministically rebuilds with identical outputs given same TEI + script version.
- Passage→token-range mapping is complete for sampled passages.
- Normalization implementation matches DB search behavior.

Dependencies:
- TEI ingest/CTS URNs stable.

---

### Phase 1 — Empirical open coding (parallel annotators)
Goal: log mention spans with minimal prior commitments.

Tasks:
1.1 Run OpenCoder A on the sample manifest.
1.2 Run OpenCoder B on the same manifest.
1.3 (Optional) OpenCoder C on “hard zones” only.

Deliverables:
- `data/annotations/open_coding/A.jsonl`
- `data/annotations/open_coding/B.jsonl`

Acceptance criteria:
- ≥ 90% of sampled passages have at least one coded mention where expected (sanity check).
- No non-allowed `provisional_type` values appear.

Dependencies:
- Phase 0 complete.

---

### Phase 2 — Agreement + adjudication (gold core)
Goal: identify systematic confusions and produce a gold dataset.

Tasks:
2.1 Compute inter-annotator agreement (IAA).
2.2 Generate adjudication queue (only disagreements + low-confidence).
2.3 Adjudicate to gold.

Deliverables:
- `reports/iaa/summary.md` + confusion matrix
- `data/annotations/adjudicated/gold_v0.jsonl`

Acceptance criteria:
- IAA report produced with per-type precision/recall proxy metrics (span overlap rules declared).
- Gold set contains explicit decisions for all queued disagreements (or explicit deferral codes).

Dependencies:
- Phase 1 complete.

---

### Phase 3 — Induce MVO from evidence (ontology v0.1)
Goal: promote only what the data supports.

Tasks:
3.1 Characterize recurrent disagreement patterns.
3.2 Propose class splits/merges and operational definitions.
3.3 Propose only relations that recur and serve queries.
3.4 Write/update guidelines with examples anchored by CTS URN.

Deliverables:
- `data/ontology/mvo.yaml` (v0.1)
- `data/ontology/relations.yaml` (v0.1)
- `docs/ontology_coding_guidelines.md`

Acceptance criteria:
- Every type/relation has: operational definition, at least 2 positive examples, and at least 1 negative/edge example.
- Every relation is justified by (a) evidence counts in gold and (b) at least one competency question it supports.
- `scripts/validate_ontology.py` passes.

Dependencies:
- Phase 2 complete.

---

### Phase 4 — Entity registry + lexicon bootstrap (linking begins)
Goal: convert gold mentions into stable entity IDs and variant lexicons.

Tasks:
4.1 Bootstrap entity candidate clusters from gold (per type).
4.2 Curate preferred labels and variants.
4.3 Create lexicon TSVs with normalized variants.
4.4 Link gold mentions to entity IDs.

Deliverables:
- `data/entities/*.tsv`
- `data/lexicons/*.tsv`
- `data/annotations/linked/gold_v0_linked.jsonl`

Acceptance criteria:
- ≥ 80% of gold mentions are linkable to an entity ID (target; revise by type).
- Unlinked mentions are classified: `new_entity`, `missing_variant`, `ambiguous`, `error`.

Dependencies:
- Phase 3 complete.

---

### Phase 5 — Scale tagging to full corpus (precision-first)
Goal: tag entire TEI set with lexicons; queue review for ambiguity.

Tasks:
5.1 Run lexicon tagging over all TEI.
5.2 Generate review queues (ambiguity, overlaps, low-confidence).
5.3 Human-in-the-loop review for queued items.
5.4 Coverage reporting per work/type.

Deliverables:
- `data/annotations/linked/auto_{workSlug}.jsonl`
- `data/annotations/linked/reviewed_{workSlug}.jsonl`
- `reports/coverage/{workSlug}.md`

Acceptance criteria:
- Precision-first pass yields manageable review volume (define threshold, e.g. ≤ 15% of mentions queued).
- No illegal types/relations in outputs (validated against MVO).
- Coverage reports highlight “blind spots” (e.g., places under-detected in author X).

Dependencies:
- Phase 4 complete.

---

### Phase 6 — Re-anchoring and TEI enrichment exports (optional)
Goal: survive TEI edits and provide TEI exports when needed.

Tasks:
6.1 Re-anchor spans after TEI changes (token fingerprinting).
6.2 Emit TEI standOff annotations generated from linked mentions.
6.3 (Optional) inline TEI tagging for stable classes only (typically PLACE/PERSON).

Deliverables:
- `reports/drift/{workSlug}.md`
- `tei/enriched/{workSlug}.xml` (standOff-first)

Acceptance criteria:
- Drift report produced on any TEI diff; failures exceed threshold -> warn or CI block (configurable).
- Enriched TEI validates as TEI P5 (if you enforce this) and preserves CTS URNs.

Dependencies:
- Phase 5 for meaningful enrichment; Phase 0/6.1 for re-anchoring.

---

## Competency questions (must drive ontology decisions)

Maintain these in `docs/ontology_coding_guidelines.md` and expand as needed:
- CQ1: “List all places of origin for material X across authors.”
- CQ2: “List all processes applied to material X (and tools used).”
- CQ3: “Show all properties attributed to material X (odor/taste/color/krasis terms).”
- CQ4: “Group synonym families and show attestations per work.”

Rule: no new relation enters MVO without mapping to at least one CQ and evidence counts.

---

## CI gates (recommended)

Warn-only initially:
- Ontology/schema validation (types/relations defined; TSV headers correct)
- Token index rebuild determinism check on a small smoke subset

Block CI once stable:
- `validate_ontology.py` fails
- `tag_with_lexicons.py` outputs illegal fields/types
- Re-anchoring drift above threshold for “required” texts

---

## Minimal happy path (one work)

One-command runner (demo mode; deterministic stand-ins for human/LLM steps):
- `python3 scripts/run_ner_ontology_one_work.py --tei-file tei/output/tlg0057.tlg075.1st1K-grc1.xml --work-slug galen_smt --mode demo --n-passages 25 --seed 0`

External (human/LLM) mode (builds token index + sample manifest, then stops with a plan file):
- `python3 scripts/run_ner_ontology_one_work.py --tei-file tei/output/tlg0057.tlg075.1st1K-grc1.xml --work-slug galen_smt --mode external --n-passages 25 --seed 0`

Human resume mode (expects `data/annotations/open_coding/A.jsonl`, `data/annotations/open_coding/B.jsonl`, `data/annotations/adjudicated/gold_v0.jsonl`, and `data/annotations/linked/reviewed_galen_smt.jsonl` to exist):
- `python3 scripts/run_ner_ontology_one_work.py --tei-file tei/output/tlg0057.tlg075.1st1K-grc1.xml --work-slug galen_smt --mode human`

1) Token index
- `python3 scripts/build_token_index.py --tei-file tei/output/tlg0057.tlg075.1st1K-grc1.xml --work-slug galen_smt --out data/token_index`

2) Sample manifest
- `python3 scripts/make_sample_manifest.py --token-index data/token_index --works galen_smt --out data/samples/sample_manifest.json --max-passage-tokens 250`

3) Open coding (A/B)
- Use Codex CLI non-interactively (recommended), reading the prompt from stdin:
  - `codex exec - < prompts/agents/opencoder_A.md`
  - `codex exec - < prompts/agents/opencoder_B.md`
- Or use the helper wrapper to force “JSONL-only” output into the target file:
  - `python3 scripts/codex_exec_jsonl.py --prompt prompts/agents/opencoder_A.md --out data/annotations/open_coding/A.jsonl`
  - `python3 scripts/codex_exec_jsonl.py --prompt prompts/agents/opencoder_B.md --out data/annotations/open_coding/B.jsonl`

4) IAA + queue
- `python3 scripts/compute_iaa.py --a data/annotations/open_coding/A.jsonl --b data/annotations/open_coding/B.jsonl --out reports/iaa/galen_smt_v0`
- `python3 scripts/make_adjudication_queue.py --a data/annotations/open_coding/A.jsonl --b data/annotations/open_coding/B.jsonl --token-index data/token_index/galen_smt.json --out data/annotations/adjudication_queue.jsonl`

5) Adjudicate
- Produce adjudicated decisions for the queue:
  - `codex exec - < prompts/agents/adjudicator.md`
  - Or: `python3 scripts/codex_exec_jsonl.py --prompt prompts/agents/adjudicator.md --out data/annotations/adjudicated/gold_v0_queue_decisions.jsonl`

Then build a full gold set (agreed items + adjudicated decisions):
- `python3 scripts/build_gold_from_open_coding.py --a data/annotations/open_coding/A.jsonl --b data/annotations/open_coding/B.jsonl --adjudicated-queue data/annotations/adjudicated/gold_v0_queue_decisions.jsonl --out data/annotations/adjudicated/gold_v0.jsonl`

6) Induce MVO
- `codex exec - < prompts/agents/ontology_inducer.md`

7) Bootstrap entities/lexicons
- `python3 scripts/bootstrap_entities_from_gold.py --gold data/annotations/adjudicated/gold_v0.jsonl --out-dir data/entities`
- `python3 scripts/build_lexicons.py --entities data/entities --out-dir data/lexicons`

8) Tag full work + review queue
- `python3 scripts/tag_with_lexicons.py --token-index data/token_index/galen_smt.json --lexicons data/lexicons --out data/annotations/linked --report reports/coverage/galen_smt.md`
- `python3 scripts/make_review_queue.py --in data/annotations/linked/auto_galen_smt.jsonl --token-index data/token_index/galen_smt.json --out data/annotations/review_queue_galen_smt.jsonl`

9) Review
- `codex exec - < prompts/agents/reviewer.md`
- Or: `python3 scripts/codex_exec_jsonl.py --prompt prompts/agents/reviewer.md --out data/annotations/linked/reviewed_galen_smt.jsonl`

10) Export TEI standOff (optional)
- `python3 scripts/export_tei_with_standoff.py --tei-file tei/output/tlg0057.tlg075.1st1K-grc1.xml --ann data/annotations/linked/reviewed_galen_smt.jsonl --out tei/enriched`

---
