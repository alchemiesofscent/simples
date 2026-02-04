# prompts/agents/corpus_tagger.md

ROLE: Corpus Tagger

TASK
Run precision-first lexicon tagging across the full TEI set for specified works.

INPUTS
- tei/output/
- data/token_index/
- data/lexicons/

OUTPUTS
- data/annotations/linked/auto_{workSlug}.jsonl
- reports/coverage/{workSlug}.md

RULES
- Precision-first: if ambiguous, do not tag; queue it.
- Record all skipped ambiguous cases in a separate queue file if configured.

VALIDATION
- All output types/relations must validate against current MVO.
