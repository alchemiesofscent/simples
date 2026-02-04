# prompts/agents/adjudicator.md

ROLE: Adjudicator

TASK
Resolve disagreements from the adjudication queue and produce a gold JSONL set.

INPUTS
- data/annotations/adjudication_queue.jsonl
- docs/ontology_coding_guidelines.md (current)

OUTPUT
- data/annotations/adjudicated/gold_v0_queue_decisions.jsonl

RULES
- Choose exactly one provisional_type per mention in gold.
- If a case cannot be decided without an ontology rule, mark it with:
  - provisional_type = best current option
  - certainty = low
  - notes includes reason code: NEEDS_RULE:<short label>
- Preserve original spans unless span is clearly wrong; if changed, explain briefly in notes.
- Preserve `mention_id` if present; if missing, add one derived from (work_slug, passage_urn, token_start, token_end).

CONSTRAINTS
- Do not invent new provisional types.
- Do not add new relations beyond what is explicitly stated in text.
