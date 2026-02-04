#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


JSONL_ONLY_SUFFIX = """

OUTPUT REQUIREMENT (STRICT)
- Your final response must be ONLY the JSONL content for the target file.
- Do not wrap in markdown. Do not add explanations.
- One JSON object per line.

SAFETY
- You MAY read the referenced input files in this repo (e.g., via cat/rg) to compute token spans.
- Do not modify any files.
- Do not run destructive shell commands.
- Do not propose or apply code changes.
- Only emit JSONL in the final response.
"""

def validate_jsonl(path: Path) -> None:
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise SystemExit(f"Codex returned empty output for {path}.")
    for i, line in enumerate(content.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except Exception as e:
            raise SystemExit(f"Invalid JSON on line {i} of Codex output: {e}\nLINE={line!r}")
        if not isinstance(obj, dict):
            raise SystemExit(f"Line {i} is not a JSON object.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Run Codex on a prompt file and capture JSONL-only output to a file.")
    ap.add_argument("--prompt", required=True, help="Prompt markdown file under prompts/agents/...")
    ap.add_argument("--out", required=True, help="Output file path to write (JSONL).")
    ap.add_argument("--cd", default=".", help="Working directory for codex exec.")
    ap.add_argument("--model", help="Optional codex model override.")
    ap.add_argument("--effort", choices=["low", "medium", "high"], default="medium", help="Model reasoning effort.")
    ap.add_argument("--no-validate", action="store_true", help="Skip JSONL validation of the captured output.")
    args = ap.parse_args()

    prompt_path = Path(args.prompt)
    out_path = Path(args.out)

    base_prompt = prompt_path.read_text(encoding="utf-8")
    final_prompt = base_prompt.rstrip() + JSONL_ONLY_SUFFIX

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    cmd = [
        "codex",
        "exec",
        "--output-last-message",
        str(tmp_path),
        "-C",
        str(Path(args.cd)),
        "-c",
        f'model_reasoning_effort="{args.effort}"',
    ]
    if args.model:
        cmd.extend(["-m", args.model])

    # Feed prompt on stdin.
    subprocess.run(cmd, input=final_prompt.encode("utf-8"), check=True)
    content = tmp_path.read_text(encoding="utf-8").strip() + "\n"
    out_path.write_text(content, encoding="utf-8")
    if not args.no_validate:
        validate_jsonl(out_path)
    tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
