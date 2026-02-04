#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from ner_ontology_utils import sha256_file, write_json


def run(cmd: list[str]) -> None:
    subprocess.check_call(cmd)


def is_empty_jsonl(path: Path) -> bool:
    if not path.exists():
        return True
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                return False
    return True


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the NER + empirical ontology MVP on a single TEI work.")
    ap.add_argument("--tei-file", required=True)
    ap.add_argument("--work-slug", required=True)
    ap.add_argument("--mode", choices=["demo", "external", "human"], default="demo")
    ap.add_argument("--max-passages", type=int, help="Optional limit for token index build (smoke runs).")
    ap.add_argument("--n-passages", type=int, default=25)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-passage-tokens", type=int, default=400)
    ap.add_argument("--out-root", default=".", help="Workspace root for outputs (default: repo root).")
    ap.add_argument("--a-jsonl", help="Open-coding A JSONL path (human mode).")
    ap.add_argument("--b-jsonl", help="Open-coding B JSONL path (human mode).")
    args = ap.parse_args()

    root = Path(args.out_root)
    tei_file = Path(args.tei_file)
    work_slug = args.work_slug

    token_index = root / "data" / "token_index"
    samples = root / "data" / "samples"
    ann = root / "data" / "annotations"
    reports = root / "reports"
    enriched = root / "tei" / "enriched"

    token_index_path = token_index / f"{work_slug}.json"
    sample_manifest_path = samples / "sample_manifest.json"

    a_path = ann / "open_coding" / "A.jsonl"
    b_path = ann / "open_coding" / "B.jsonl"
    iaa_dir = reports / "iaa" / f"{work_slug}_v0"
    queue_path = ann / "adjudication_queue.jsonl"
    gold_path = ann / "adjudicated" / "gold_v0.jsonl"
    adjudicated_queue_path = ann / "adjudicated" / "gold_v0_queue_decisions.jsonl"
    entities_dir = root / "data" / "entities"
    lexicons_dir = root / "data" / "lexicons"
    gold_linked_path = ann / "linked" / "gold_v0_linked.jsonl"
    unlinked_path = ann / "unlinked_queue.jsonl"
    auto_dir = ann / "linked"
    auto_path = auto_dir / f"auto_{work_slug}.jsonl"
    coverage_report = reports / "coverage" / f"{work_slug}.md"
    review_queue_path = ann / f"review_queue_{work_slug}.jsonl"
    reviewed_path = ann / "linked" / f"reviewed_{work_slug}.jsonl"
    enriched_path = enriched / tei_file.name

    start = time.time()

    run(["python3", "scripts/build_token_index.py", "--tei-file", str(tei_file), "--work-slug", work_slug, "--out", str(token_index)])
    if args.max_passages:
        # Rebuild in-place with max-passages if requested (keeps CLI compatible without adding a second output).
        run(
            [
                "python3",
                "scripts/build_token_index.py",
                "--tei-file",
                str(tei_file),
                "--work-slug",
                work_slug,
                "--out",
                str(token_index),
                "--max-passages",
                str(args.max_passages),
            ]
        )

    run(
        [
            "python3",
            "scripts/make_sample_manifest.py",
            "--token-index",
            str(token_index),
            "--works",
            work_slug,
            "--out",
            str(sample_manifest_path),
            "--n-passages",
            str(args.n_passages),
            "--seed",
            str(args.seed),
            "--max-passage-tokens",
            str(args.max_passage_tokens),
        ]
    )

    if args.mode == "external":
        # Stop after creating the inputs for humans/LLMs; validate what exists so far.
        manifest = {
            "work_slug": work_slug,
            "tei_file": str(tei_file),
            "tei_sha256": sha256_file(tei_file),
            "token_index": str(token_index_path),
            "sample_manifest": str(sample_manifest_path),
            "next_steps": [
                f"Produce open coding outputs: {a_path} and {b_path}",
                f"Then run IAA: python3 scripts/compute_iaa.py --a {a_path} --b {b_path} --out {iaa_dir}",
            ],
        }
        write_json(reports / "runs" / f"{work_slug}_external_plan.json", manifest)
        print("OK (external mode). See run plan at:", reports / "runs" / f"{work_slug}_external_plan.json")
        return

    if args.mode == "human":
        a_src = Path(args.a_jsonl) if args.a_jsonl else a_path
        b_src = Path(args.b_jsonl) if args.b_jsonl else b_path
        if not a_src.exists() or not b_src.exists():
            raise SystemExit(
                "human mode requires existing open-coding outputs.\n"
                f"- expected: {a_src}\n"
                f"- expected: {b_src}\n"
                "Run in external mode first, then generate these files (Codex/human)."
            )
        # Copy into canonical locations if custom paths were provided.
        if a_src != a_path:
            a_path.parent.mkdir(parents=True, exist_ok=True)
            a_path.write_text(a_src.read_text(encoding="utf-8"), encoding="utf-8")
        if b_src != b_path:
            b_path.parent.mkdir(parents=True, exist_ok=True)
            b_path.write_text(b_src.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        run(
            [
                "python3",
                "scripts/demo_open_coding.py",
                "--manifest",
                str(sample_manifest_path),
                "--annotator-id",
                "A",
                "--out",
                str(a_path),
                "--seed",
                "1",
            ]
        )
        run(
            [
                "python3",
                "scripts/demo_open_coding.py",
                "--manifest",
                str(sample_manifest_path),
                "--annotator-id",
                "B",
                "--out",
                str(b_path),
                "--seed",
                "2",
            ]
        )

    # Guideline + bounds checks for Phase 1 outputs (sources of truth: docs).
    run(["python3", "scripts/validate_guidelines.py", "--strict", "--phase", "open_coding", "--jsonl", str(a_path), str(b_path)])
    run(
        [
            "python3",
            "scripts/validate_annotations.py",
            "--mvo",
            "data/ontology/mvo.yaml",
            "--relations",
            "data/ontology/relations.yaml",
            "--token-index",
            str(token_index_path),
            "--ann",
            str(a_path),
        ]
    )
    run(
        [
            "python3",
            "scripts/validate_annotations.py",
            "--mvo",
            "data/ontology/mvo.yaml",
            "--relations",
            "data/ontology/relations.yaml",
            "--token-index",
            str(token_index_path),
            "--ann",
            str(b_path),
        ]
    )

    run(["python3", "scripts/compute_iaa.py", "--a", str(a_path), "--b", str(b_path), "--out", str(iaa_dir)])
    run(["python3", "scripts/make_adjudication_queue.py", "--a", str(a_path), "--b", str(b_path), "--token-index", str(token_index_path), "--out", str(queue_path)])
    if args.mode == "demo":
        run(["python3", "scripts/demo_adjudicate.py", "--in", str(queue_path), "--out", str(adjudicated_queue_path)])
    else:
        # In human mode, adjudication is external; accept either queue decisions or a prebuilt gold file.
        if not adjudicated_queue_path.exists() and not gold_path.exists():
            raise SystemExit(
                "human mode requires either:\n"
                f"- adjudicated queue decisions at {adjudicated_queue_path}, OR\n"
                f"- a full gold file at {gold_path}\n"
                f"Populate from {queue_path}, then rerun."
            )

    # Build a full gold set (agreed items + adjudicated queue decisions) unless already provided.
    if not gold_path.exists() or args.mode == "demo":
        run(
            [
                "python3",
                "scripts/build_gold_from_open_coding.py",
                "--a",
                str(a_path),
                "--b",
                str(b_path),
                "--adjudicated-queue",
                str(adjudicated_queue_path),
                "--out",
                str(gold_path),
            ]
        )
    run(["python3", "scripts/bootstrap_entities_from_gold.py", "--gold", str(gold_path), "--out-dir", str(entities_dir)])

    # Guideline + bounds checks for gold set (still provisional types).
    run(["python3", "scripts/validate_guidelines.py", "--strict", "--phase", "gold", "--jsonl", str(gold_path)])
    run(
        [
            "python3",
            "scripts/validate_annotations.py",
            "--mvo",
            "data/ontology/mvo.yaml",
            "--relations",
            "data/ontology/relations.yaml",
            "--token-index",
            str(token_index_path),
            "--ann",
            str(gold_path),
        ]
    )

    run(["python3", "scripts/build_lexicons.py", "--entities", str(entities_dir), "--out-dir", str(lexicons_dir)])
    run(["python3", "scripts/link_mentions.py", "--in", str(gold_path), "--lexicons", str(lexicons_dir), "--out", str(gold_linked_path), "--unlinked", str(unlinked_path)])
    run(["python3", "scripts/tag_with_lexicons.py", "--token-index", str(token_index_path), "--lexicons", str(lexicons_dir), "--out", str(auto_dir), "--report", str(coverage_report)])
    run(["python3", "scripts/make_review_queue.py", "--in", str(auto_path), "--token-index", str(token_index_path), "--out", str(review_queue_path)])
    if args.mode == "demo":
        if is_empty_jsonl(review_queue_path):
            copy_file(auto_path, reviewed_path)
        else:
            run(["python3", "scripts/demo_review.py", "--in", str(review_queue_path), "--out", str(reviewed_path)])
    else:
        if not reviewed_path.exists():
            if is_empty_jsonl(review_queue_path):
                copy_file(auto_path, reviewed_path)
            else:
                raise SystemExit(
                    "human mode requires a reviewed linked file at:\n"
                    f"- {reviewed_path}\n"
                    "Populate it from data/annotations/review_queue_{workSlug}.jsonl, then rerun."
                )
    run(["python3", "scripts/export_tei_with_standoff.py", "--tei-file", str(tei_file), "--ann", str(reviewed_path), "--out", str(enriched)])
    run(["python3", "scripts/validate_ontology.py", "--mvo", "data/ontology/mvo.yaml", "--relations", "data/ontology/relations.yaml", "--entities", str(entities_dir), "--lexicons", str(lexicons_dir)])
    run(["python3", "scripts/validate_annotations.py", "--mvo", "data/ontology/mvo.yaml", "--relations", "data/ontology/relations.yaml", "--token-index", str(token_index_path), "--ann", str(auto_path)])

    elapsed_s = round(time.time() - start, 3)
    run_manifest: dict[str, Any] = {
        "work_slug": work_slug,
        "tei_file": str(tei_file),
        "tei_sha256": sha256_file(tei_file),
        "mode": args.mode,
        "seed": args.seed,
        "n_passages": args.n_passages,
        "outputs": {
            "token_index": str(token_index_path),
            "sample_manifest": str(sample_manifest_path),
            "open_coding_A": str(a_path),
            "open_coding_B": str(b_path),
            "iaa_dir": str(iaa_dir),
            "adjudication_queue": str(queue_path),
            "gold_v0_queue_decisions": str(adjudicated_queue_path),
            "gold_v0": str(gold_path),
            "entities_dir": str(entities_dir),
            "lexicons_dir": str(lexicons_dir),
            "gold_v0_linked": str(gold_linked_path),
            "auto_linked": str(auto_path),
            "review_queue": str(review_queue_path),
            "reviewed": str(reviewed_path),
            "enriched_tei": str(enriched_path),
            "coverage_report": str(coverage_report),
        },
        "elapsed_seconds": elapsed_s,
    }
    suffix = "demo_run" if args.mode == "demo" else "human_run"
    run_path = reports / "runs" / f"{work_slug}_{suffix}.json"
    write_json(run_path, run_manifest)
    print("OK. Run manifest:", run_path)


if __name__ == "__main__":
    main()
