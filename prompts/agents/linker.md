# prompts/agents/linker.md

ROLE: Linker

TASK
Link mention annotations to entity IDs using lexicons. Produce linked JSONL and an “unlinked” queue.

INPUTS
- data/annotations/adjudicated/gold_v0.jsonl
- data/lexicons/*.tsv

OUTPUTS
- data/annotations/linked/gold_v0_linked.jsonl
- data/annotations/unlinked_queue.jsonl

RULES
- Link by normalized surface match first; if multiple matches, mark ambiguous and push to unlinked queue.
- Never silently choose among ambiguous candidates.
- Preserve original mention spans.

FIELDS
Add:
- entity_id (when linked)
- link_method (exact_norm | variant_norm | manual)
- link_confidence (low|med|high)
