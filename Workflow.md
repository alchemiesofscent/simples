# Workflow.md
# Workflow for rapid, stable, production-ready development with CLI AI agents

This workflow is optimized for “fast iterations with hard gates.” It assumes a terminal AI agent can edit files, but CI decides correctness.

## 0) One-time setup (repo conventions)

- Ensure CI runs: tests, lint, type checks, validators.
- Define “profiles”:
  - fast PR gate set (minutes)
  - nightly gate set (longer: fuzz/PBT/mutation where applicable)
- Store contracts in `docs/contracts/`.
- Store export schemas in `schemas/exports/`.

## 1) Task initiation (Spec agent)

Create a task brief (file or issue comment) using this template:

Title:
Goal:
Non-goals:
Acceptance criteria:
Edge cases:
Files likely touched:
Tests to add/update:
Risks:
DoD checklist:

Output: a single, unambiguous task brief.

## 2) Test-first pass (Test agent)

- Add failing tests that encode the acceptance criteria.
- Add at least one negative case:
  - invalid inputs
  - boundary conditions
- If ingestion/parsing is involved:
  - add a fixture file that reproduces the case.

Run the fast local gate set.
Stop if tests don’t fail for the right reason.

## 3) Implementation pass (Implementation agent)

- Implement the smallest change that makes the new tests pass.
- Avoid refactoring unless strictly necessary for correctness.
- Prefer deterministic transforms and explicit ordering.

Run the fast local gate set:
- unit tests
- lint/format
- type checks
- migration apply (if relevant)

## 4) Adversarial pass (Adversarial agent)

Decide which adversarial techniques apply:

A) Property-based tests
Use for invariants (idempotence, normalization stability, ordering, serialization round-trip).

B) Fuzzing
Use for parsers, file ingestion, schema decoding.

C) Mutation testing (selective)
Use for critical modules where coverage looks high but failure detection is uncertain.

D) LLM threat cases (only if your app calls models)
Add prompt-injection and output-validation tests.

Add at least one adversarial regression if the change is non-trivial.

## 5) Review pass (Reviewer agent + human)

Reviewer agent checklist:
- Does the diff match the acceptance criteria and nothing more?
- Are there missing edge cases?
- Are repo contracts violated (TEI/CTS, DB semantics, exports)?
- Is there any security hazard (unsafe parsing, injection, secrets)?

Human checklist:
- Are tests meaningful?
- Are failure messages actionable?
- Is the change small enough to reason about?

## 6) Quality gates (CI)

Required PR gates:
- Full unit/integration test suite (or documented profile)
- Lint/format/type checks
- Validators (TEI/indexer/export schema)
- Determinism checks where applicable

Optional nightly gates:
- Extended fuzzing runs
- Mutation testing on selected packages/modules
- Large-scale adversarial corpus runs

## 7) Merge and release hygiene

Before merge:
- Ensure the task brief DoD items are checked.
- Ensure export schemas are unchanged or version-bumped intentionally.
- Ensure migrations apply cleanly from a fresh DB.

After merge:
- If you changed an exported interface (lemma package), cut a versioned release artifact and record:
  - export_version
  - normalization/tokenizer version
  - schema version

## 8) Practical “fast path” for small fixes

If the change is truly trivial:
- add/adjust a unit test
- implement fix
- run fast gates
- merge after CI is green

If you skip tests, treat it as a prototype branch, not mergeable work.

## 9) Suggested automation hooks

- Pre-commit: format + lint + quick tests
- CI: deterministic validators + schema checks
- Nightly: fuzz/PBT/mutation jobs + drift detection reports

## 10) Definition of Done (DoD)

A change is “done” only when:
- acceptance tests pass
- at least one negative/adversarial case exists for non-trivial changes
- CI gates are green
- contracts remain satisfied
- documentation updated where behavior or interface changed
