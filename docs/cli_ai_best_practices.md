# docs/cli_ai_best_practices.md
# Best practices for building production software with CLI terminal AI coding agents

This document assumes a development style where a terminal AI model proposes code changes, but humans and automation enforce correctness, security, and maintainability. The core thesis is simple: AI increases throughput; quality comes from gates.

## 1) Operating principles

1. Make the test suite, linters, and type checks the arbiter of truth.
   - Treat AI output as untrusted until it passes the full gate set.
2. Prefer small, reversible changes.
   - One task → one patch series → one merged unit.
3. Keep “specification” close to code.
   - Invariants go into tests, schema constraints, and fixtures.
4. Separate authority:
   - Humans own requirements and acceptance criteria.
   - CI owns pass/fail.
   - AI owns proposing diffs.

## 2) Evidence base (what’s well-supported)

Test-first practices:
- Industrial and controlled studies report substantial reductions in pre-release defect density when teams adopt TDD, with some increase in initial development time. (Nagappan et al., Microsoft; Madeyski)
- Conclusion: use TDD where defects are expensive and interfaces are evolving; do not fetishize it where exploration is the goal.

Mutation testing:
- Empirical analyses show mutation testing reveals gaps not captured by conventional coverage, and helps diagnose tool/test weaknesses. (Kintis et al.)
- Conclusion: use mutation testing selectively (critical modules; PR gates for high-risk code paths).

Property-based testing (PBT):
- Empirical evaluation in Python indicates PBT can find real bugs and has tradeoffs in developer effort and test design. (Ravi & Coblentz)
- Conclusion: use PBT for core invariants (parsers, normalizers, tokenizers, transformations).

Fuzzing:
- Large-scale studies of continuous fuzzing (e.g., OSS-Fuzz) show it discovers vulnerabilities/bugs over time, especially for input-heavy components.
- Conclusion: fuzz parsers and format handlers, and keep fuzzing running continuously.

AI coding assistants:
- Controlled experiments and field evidence show AI pair programmers can speed task completion, but security studies show a substantial fraction of generated code can be vulnerable if ungated. (Peng et al.; Pearce et al.; OpenSSF guidance)
- Conclusion: couple AI coding with mandatory quality and security gates.

LLM adversarial testing:
- OWASP LLM Top 10 provides a threat taxonomy (prompt injection, insecure output handling, etc.).
- NIST GenAI profiles emphasize adversarial role-playing/red teaming/chaos testing as part of test and evaluation.
- Conclusion: build red-team cases into the test corpus, and run them continuously.

Evaluation loops:
- Treat evaluation sets as living assets; run evals continuously and grow them as failures appear. (OpenAI evaluation best practices)
- Conclusion: every incident becomes a regression test or eval item.

## 3) Test-driven development (TDD) practices for AI-assisted coding

Goal: reduce integration churn and hallucinated “design drift” by forcing the system to prove behavior.

Recommended TDD loop (tight):
1. Write or update an acceptance test (unit/integration) that fails for the intended change.
2. Ask the AI to implement the smallest change to pass the test.
3. Run local gates; only then expand scope.

Best practices:
- Put invariants in tests, not in docstrings.
- Use “contract tests” for boundaries (DB schema constraints, file formats, parsers).
- Keep fixtures small and realistic; add edge-case fixtures as soon as they bite you.

When not to use strict TDD:
- UI layout experiments, spike prototypes, or one-off scripts. In these cases, still require a “stabilization pass” where tests are added before merge.

## 4) Adversarial testing (beyond happy paths)

Adversarial testing here means: intentional inputs and scenarios designed to break assumptions.

4.1 Traditional software adversarial testing
- Fuzzing: for parsers and ingestion (TEI parsing, XML handling, normalization).
- Property-based tests: for invariants (idempotence, normalization stability, ordering).
- Mutation testing: for “is the test suite meaningful?”

4.2 LLM-specific adversarial testing (if your app calls models)
- Prompt injection cases (direct and indirect).
- Output-format violations (schema breaks).
- Data exfiltration attempts (secrets in prompt/context).
- Tool-abuse attempts (path traversal, arbitrary command requests, privilege escalation).

How to operationalize:
- Maintain an “adversarial corpus” folder of prompts/inputs.
- Every discovered failure becomes a test or an eval case.
- Run adversarial tests in CI (fast subset) and nightly (full corpus).

## 5) Sub-agent workflow automation (how to use multiple agents without chaos)

The most reliable pattern is role separation plus explicit handoffs.

Canonical sub-agents:
1. Spec agent: turns a request into acceptance criteria + constraints + edge cases.
2. Test agent: writes failing tests and fixtures.
3. Implementation agent: makes code changes to pass tests.
4. Reviewer agent: audits for security, correctness, and maintainability; proposes deltas.
5. Adversarial agent: adds negative cases (fuzz/PBT/mutation suggestions).
6. Release agent: updates docs/changelog, bumps versions, checks reproducibility.

Best practices:
- Every agent output must be machine-checkable (tests, schema, lint, type checks).
- Keep an explicit “task file” (see Workflow.md) that records:
  - scope, acceptance, out-of-scope
  - gate results
  - risk notes
- Enforce “stop-the-line” rules: no merge if core gates fail.

## 6) Quality gating (what must be true before merge)

Define a gating ladder so you can move fast without being reckless.

Local gates (developer machine):
- Unit tests for touched modules
- Formatting + lint
- Type checks (where present)
- Security scan basics (dependency + secret scan)

PR/CI gates (required):
- Full test suite (or a defined profile per change type)
- Lint/format/type checks
- Schema migrations validated (apply cleanly)
- Determinism checks for ingestion pipelines (same input → same output)
- Export schema validation (JSON schema for published artifacts)

Release gates (before tagging):
- Reproducible build steps documented and validated
- Smoke test in a clean environment
- Backward-compatibility checks for exported interfaces (lemma IDs, schemas)

## 7) Templates you should standardize

1. Task brief template (one per change)
- Goal
- Non-goals
- Acceptance criteria
- Tests to add/update
- Risks
- Rollback plan

2. Definition of Done (DoD) checklist
- Tests added/updated
- Negative/adversarial cases added if applicable
- CI green
- Docs updated
- Migration tested (if any)
- Export interfaces versioned and validated (if any)

## References (URLs)
- Nagappan et al., “Realizing Quality Improvement Through Test-Driven Development: Results and Experiences of Four Industrial Teams” (Microsoft Research)
- Madeyski, “The Impact of Test-Driven Development on Software Development Productivity – An Empirical Study”
- Kintis et al., “How effective are mutation testing tools? An empirical analysis…” (EMSE)
- Ravi & Coblentz, “An Empirical Evaluation of Property-Based Testing in Python” (OOPSLA 2025)
- Large-Scale Empirical Analysis of Continuous Fuzzing (OSS-Fuzz)
- Peng et al., “The Impact of AI on Developer Productivity: Evidence from GitHub Copilot”
- Pearce et al., “Asleep at the Keyboard? Assessing the Security of GitHub Copilot’s Code Contributions”
- OpenSSF Best Practices: Security-Focused Guide for AI Code Assistant Instructions
- OWASP Top 10 for Large Language Model Applications
- NIST AI 600-1 GenAI Profile (adversarial testing / red teaming guidance)
- OpenAI: Evaluation best practices (continuous evaluation)
