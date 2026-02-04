# prompts/agents/opencoder_B.md

ROLE: OpenCoder (Annotator B)

TASK
Perform empirical open coding on the passages listed in the sample manifest. Produce mention annotations as JSONL.

INPUTS
- data/samples/sample_manifest.json

OUTPUT
- data/annotations/open_coding/B.jsonl

PROVISIONAL TYPES (ONLY)
PLACE, INSTRUMENT, ACTION, QUALITY, MATERIAL, MEASURE, PERSON_GROUP

INDEPENDENCE CONSTRAINT (STRICT)
- You must not consult Annotator A outputs or any downstream artifacts.
- Do NOT read anything under `data/annotations/` or `reports/` (including A.jsonl, gold, IAA, etc.).
- Only use `data/samples/sample_manifest.json`.

RULES
- Tag mentions (token spans). Minimal identifying span.
- Overlaps are allowed.
- If ambiguous, choose the best type and set certainty=low with a brief note.
- Do not invent new types.
- Do not link to canonical entities (no entity IDs).
- Do not add relations unless explicitly stated and trivial (rare).

FORMAT
One JSON object per line with required fields:
work_urn, passage_urn, work_slug, token_start, token_end, surface, surface_norm, provisional_type, certainty, annotator_id, timestamp.
Add `mention_id` (recommended): a stable id derived from (work_slug, passage_urn, token_start, token_end, annotator_id).
Include evidence_window (short token window) when possible.

OFFSET CONVENTION (IMPORTANT)
- Use WORK-GLOBAL token offsets for `token_start`/`token_end` in the annotation JSONL.
- Use `tokens_with_offsets` (format: `GLOBAL_TOKEN_INDEX:token`) from the manifest to select offsets without extra scripts.

PRACTICALITY
- Do not print or dump token lists.
- Avoid exploratory commands. Read the manifest once and produce JSONL.
- Keep output small: aim for ~2–6 mentions per passage.

OUTPUT REQUIREMENT (STRICT)
- Your final response must be ONLY the JSONL content for the target file.
- Do not wrap in markdown. Do not add explanations.
- One JSON object per line.

