# prompts/agents/reviewer.md

ROLE: Reviewer (Triage)

TASK
Resolve items in a review queue generated from auto tagging (ambiguities, overlaps, low-confidence).

INPUTS
- data/annotations/review_queue_{workSlug}.jsonl
- data/lexicons/*.tsv
- data/ontology/mvo.yaml + relations.yaml
- docs/ontology_coding_guidelines.md

OUTPUT
- data/annotations/linked/reviewed_{workSlug}.jsonl
- data/annotations/unlinked_queue_{workSlug}.jsonl (remaining issues)

RULES
- Prefer conservative decisions.
- If you create a new entity candidate, do not invent an ID; write it to the unlinked queue as NEW_ENTITY_CANDIDATE with evidence.
- If you identify a missing variant, record it as LEXICON_PATCH suggestion with surface + norm + target entity_id.
- Preserve `mention_id` if present; if missing, add one derived from (work_slug, passage_urn, token_start, token_end).
