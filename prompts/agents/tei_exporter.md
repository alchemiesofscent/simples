# prompts/agents/tei_exporter.md

ROLE: TEI Exporter

TASK
Generate enriched TEI with standOff annotations from linked mention JSONL.

INPUTS
- tei/output/{workSlug}.xml
- data/annotations/linked/reviewed_{workSlug}.jsonl
- data/ontology/mvo.yaml + relations.yaml

OUTPUTS
- tei/enriched/{workSlug}.xml

REQUIREMENTS
- Do not alter the base text content.
- Add standOff markup only (default).
- Preserve CTS URNs unchanged.
- Emit stable xml:id for spans; reference CTS passage + token offsets in attributes or notes.

CONSTRAINT
Inline tagging is optional and must be limited to stable classes only if explicitly requested (default: no inline tags).
