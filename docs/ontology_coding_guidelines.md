# docs/ontology_coding_guidelines.md

# Ontology coding guidelines (empirical / operational)

Status: draft. This document is updated by the adjudication + ontology induction phases.

## Scope
We annotate *mentions* (attestations in text), not abstract concepts. A mention is a token span anchored to a CTS passage and token offsets. Mentions may overlap.

## Phase 1 provisional types (only)
- PLACE
- INSTRUMENT
- ACTION
- QUALITY
- MATERIAL
- MEASURE
- PERSON_GROUP

Rule: If unsure, choose the best provisional type and set `certainty=low` with a brief note. Do not invent new types.

## Span rules
- Tag the minimal span that identifies the mention.
- Include attached modifiers only if they disambiguate the referent (e.g., “burnt X” may be two mentions: QUALITY/STATE and MATERIAL).
- Allow overlaps; do not “force” disjoint spans.

## Common confusions (handle by rule, not intuition)
- QUALITY vs MATERIAL: adjectives go QUALITY unless lexicalized as a known drug form; record both if needed.
- ACTION vs INSTRUMENT: verbs and verbal nouns trend ACTION; concrete containers/implements trend INSTRUMENT.
- PLACE as origin: ethnics/toponyms that signal provenance count as PLACE; annotate the place string itself.

## Relations (Phase 1)
Avoid relations in open coding unless the relation is explicit and trivial (e.g., “called X” → synonym hint). Most relations are added after the gold set exists.

## Competency questions (must motivate MVO)
CQ1 Origins: places of origin for material X across works.
CQ2 Operations: processes applied to X; tools used.
CQ3 Properties: properties attributed to X.
CQ4 Synonym families: variant names and attestations.

Add a new CQ before adding a new relation class.

## Evidence bookkeeping
Any proposed new type/relation for MVO must include:
- Evidence count in gold (number of distinct attestations)
- At least two positive examples (CTS URNs)
- At least one negative/edge example (CTS URN)
- Which CQ it supports
