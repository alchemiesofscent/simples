# prompts/agents/opencoder_A.md

ROLE: OpenCoder (Annotator A)

TASK
Perform empirical open coding on the passages listed in the sample manifest. Produce mention annotations as JSONL.

INPUTS
- data/samples/sample_manifest.json
- data/token_index/{workSlug}.json

OUTPUT
- data/annotations/open_coding/A.jsonl

PROVISIONAL TYPES (ONLY)
PLACE, INSTRUMENT, ACTION, QUALITY, MATERIAL, MEASURE, PERSON_GROUP

RULES
- Tag mentions (token spans). Minimal identifying span.
- Overlaps are allowed.
- If ambiguous, choose the best type and set certainty=low with a brief note.
- Do not invent new types.
- Do not link to canonical entities (no entity IDs).
- Do not add relations unless the relation is explicitly stated and trivial (rare).

FORMAT
One JSON object per line with required fields:
work_urn, passage_urn, work_slug, token_start, token_end, surface, surface_norm, provisional_type, certainty, annotator_id, timestamp.
Add `mention_id` (recommended): a stable id derived from (work_slug, passage_urn, token_start, token_end, annotator_id).
Include evidence_window (short token window) when possible.

OFFSET CONVENTION (IMPORTANT)
- Use WORK-GLOBAL token offsets for `token_start`/`token_end` in the annotation JSONL.
- `data/samples/sample_manifest.json` includes passage bounds as `passage_token_start`/`passage_token_end` (and also `token_start`/`token_end` for the passage).
- If you choose a span using passage-local indices, convert to global offsets by adding `passage_token_start`.

QUALITY BAR
Prefer precision over recall. Avoid speculative tagging.

PRACTICALITY (IMPORTANT)
- Do not print or dump long token lists.
- Avoid exploratory commands (no ad-hoc Python scripts that print hundreds of tokens).
- Use the tokens already present in `data/samples/sample_manifest.json` to pick spans.
- Keep output small: aim for ~2–6 mentions per passage unless a passage is dense.
- Prefer using `tokens_with_offsets` (format: `GLOBAL_TOKEN_INDEX:token`) to select spans without needing any extra scripts.
