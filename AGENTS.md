# agents.md
# Working with CLI terminal AI agents in this repo

This repo assumes AI-assisted development, but correctness is enforced by gates. AI is a contributor, not an authority.

## 1) Ground rules

- No change merges unless required CI gates pass.
- AI-generated code is treated as untrusted until tests + lint + type checks pass.
- Prefer small PRs; do not batch unrelated refactors with feature work.
- Preserve repository contracts:
  - CTS/TEI invariants
  - schema constraints
  - export schemas (public interface)

## 2) Default agent roles and handoffs

Use these roles explicitly in prompts and commits.

Spec agent
- Produces: task brief, acceptance criteria, edge cases, risk list, DoD checklist.

Test agent
- Produces: failing unit/integration tests + fixtures, plus adversarial cases where relevant.

Implementation agent
- Produces: minimal code changes to pass tests.

Reviewer agent
- Produces: security + correctness review notes, proposes changes, verifies gates.

Adversarial agent
- Produces: negative tests (PBT/fuzz seeds), prompt-injection cases if LLM features exist, mutation-testing suggestions.

Release agent
- Produces: export artifacts, schema validation, documentation updates, release notes.

## 3) Standard quality gates (must run)

Local (before pushing)
- format + lint
- unit tests for touched modules
- migration apply (if you changed SQL)
- deterministic pipeline checks (if you touched ingestion/indexing)

CI (required for merge)
- full test suite (or CI profile documented in Workflow.md)
- export schema validation (if export changes)
- TEI/ingestion validator checks (if TEI pipeline changes)

## 4) Repo contracts that agents must not violate

TEI / CTS invariants
- Do not change CTS passage structure or `div[@type="textpart"]/@n` hierarchy.
- Do not reorder base text.
- Do not move `<pb>` / `<lb>` relative to the text.

Database invariants
- Derived cache fields are overwritten only by the indexer, not edited in-app.
- SQL-owned fields (translations, lemma links, annotations, assertions) persist across re-indexing.

Public interface invariants (for cookbook integration)
- lemma_id is stable and never renumbered.
- lemma package export schema is versioned; changes are backwards-compatible unless explicitly bumped.

## 5) Prompting conventions (CLI agents)

When asking an agent to implement:
- Provide file paths, current constraints, and acceptance tests.
- Instruct: “Make the smallest change that passes the tests.”
- Require: “Run gates and report results.”

When asking an agent to review:
- Require: “List concrete risks + specific diff suggestions.”
- Require: “Verify no contract invariants were violated.”

## 6) Required artifacts per task

Every substantive change must produce:
- Updated/added tests
- Updated docs if contracts changed
- A short task log in the PR description or in `docs/reports/` (optional) stating:
  - what changed
  - how it was tested
  - any known limitations

## 7) Stop-the-line criteria

Do not merge if any of these are true:
- Tests failing
- Migration does not apply cleanly
- Determinism regressions (same input produces different output)
- Export schema validation fails
- TEI/CTS invariants violated
- Security scan flags unresolved high-severity issues
