# prompts/agents/iaa_evaluator.md

ROLE: IAA Evaluator

TASK
Compute inter-annotator agreement between two open-coding JSONL files.

INPUTS
- data/annotations/open_coding/A.jsonl
- data/annotations/open_coding/B.jsonl

OUTPUTS
- reports/iaa/summary.md
- confusion matrix by provisional_type
- list of top disagreement clusters (with CTS URNs)

SPAN MATCHING RULE
Define and use a clear rule (must be stated in the report), e.g.:
- Exact match on (passage_urn, token_start, token_end), OR
- Overlap ≥ 0.5 Jaccard on token span within same passage_urn

CONSTRAINTS
- Do not alter annotations.
- Do not propose ontology changes here; only report empirical failures.

DELIVERABLE REQUIREMENTS
- Per-type agreement
- Most frequent confusions
- Examples (CTS URNs) for each major confusion
