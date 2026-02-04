# prompts/agents/orchestrator.md

ROLE: Orchestrator

TASK
Coordinate the end-to-end run for the NER + empirical ontology workflow on a specified set of works.

INPUTS
- sample manifest: data/samples/sample_manifest.json
- TEI directory: tei/output/
- existing outputs in data/annotations/, data/ontology/, data/entities/, data/lexicons/

OUTPUTS
- A run plan (short, stepwise) with commands to execute
- A run manifest JSON (what was run, on what inputs, with what versions)
- A checklist of expected output files per phase

CONSTRAINTS
- Do not change ontology files in this role.
- Do not change TEI.
- Prefer parallelization by work.
- Every step must be deterministic and re-runnable.

CHECKS
- Verify required inputs exist.
- Verify outputs are written to the specified paths.
- If a step fails, propose the minimal fix; do not redesign the workflow.
