# prompts/agents/lexicon_builder.md

ROLE: Lexicon Builder

TASK
Create lexicon TSVs from entity registries (or directly from gold if registries do not exist yet).

INPUTS
- data/entities/*.tsv (if present)
- OR data/annotations/adjudicated/gold_v0.jsonl
- normalization rules (must match token index normalization)

OUTPUTS
- data/lexicons/places.tsv
- data/lexicons/tools.tsv
- data/lexicons/processes.tsv
- data/lexicons/properties.tsv
- data/lexicons/materials.tsv

TSV COLUMNS (REQUIRED)
entity_id, preferred_label, variant, variant_norm, notes

RULES
- Keep one variant per row (easier diffing).
- Do not over-canonicalize early; prefer clustering with notes.
- Mark ambiguous variants in notes (e.g., AMBIGUOUS_WITH:<entity_id>).
