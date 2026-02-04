#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ner_ontology_utils import PROVISIONAL_TYPES, iter_jsonl


def jaccard(a0: int, a1: int, b0: int, b1: int) -> float:
    inter = max(0, min(a1, b1) - max(a0, b0))
    union = (a1 - a0) + (b1 - b0) - inter
    return (inter / union) if union else 0.0


def best_match(target: dict[str, Any], candidates: list[dict[str, Any]], threshold: float) -> dict[str, Any] | None:
    best: tuple[float, dict[str, Any]] | None = None
    for c in candidates:
        s = jaccard(int(target["token_start"]), int(target["token_end"]), int(c["token_start"]), int(c["token_end"]))
        if s < threshold:
            continue
        if best is None or s > best[0]:
            best = (s, c)
    return best[1] if best else None


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute IAA between two open-coding JSONL files.")
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--out-dir", help="Output directory.")
    ap.add_argument("--out", help="Alias for --out-dir (docs/wbs_ner_ontology.md compatibility).")
    ap.add_argument("--match", choices=["exact", "overlap50"], default="overlap50")
    args = ap.parse_args()

    out_base = args.out_dir or args.out
    if not out_base:
        raise SystemExit("Provide --out-dir (or --out).")
    out_dir = Path(out_base)
    out_dir.mkdir(parents=True, exist_ok=True)

    a = list(iter_jsonl(Path(args.a)))
    b = list(iter_jsonl(Path(args.b)))

    by_passage_a: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_passage_b: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in a:
        by_passage_a[str(r["passage_urn"])].append(r)
    for r in b:
        by_passage_b[str(r["passage_urn"])].append(r)

    threshold = 1.0 if args.match == "exact" else 0.5

    confusion: Counter[tuple[str, str]] = Counter()
    matched = 0
    total_a = len(a)
    total_b = len(b)
    disagreements: list[dict[str, Any]] = []

    for passage_urn in sorted(set(by_passage_a) | set(by_passage_b)):
        aa = sorted(by_passage_a.get(passage_urn, []), key=lambda r: (r["token_start"], r["token_end"]))
        bb = sorted(by_passage_b.get(passage_urn, []), key=lambda r: (r["token_start"], r["token_end"]))
        used_b: set[int] = set()

        for ra in aa:
            if args.match == "exact":
                mb = None
                for i, rb in enumerate(bb):
                    if i in used_b:
                        continue
                    if int(ra["token_start"]) == int(rb["token_start"]) and int(ra["token_end"]) == int(rb["token_end"]):
                        mb = rb
                        used_b.add(i)
                        break
            else:
                mb = best_match(ra, [rb for i, rb in enumerate(bb) if i not in used_b], threshold)
                if mb is not None:
                    for i, rb in enumerate(bb):
                        if rb is mb:
                            used_b.add(i)
                            break

            if mb is None:
                disagreements.append({"passage_urn": passage_urn, "a": ra, "b": None, "reason": "missing_in_B"})
                continue

            matched += 1
            ta = str(ra.get("provisional_type"))
            tb = str(mb.get("provisional_type"))
            confusion[(ta, tb)] += 1
            if ta != tb:
                disagreements.append({"passage_urn": passage_urn, "a": ra, "b": mb, "reason": "type_mismatch"})

        for i, rb in enumerate(bb):
            if i not in used_b:
                disagreements.append({"passage_urn": passage_urn, "a": None, "b": rb, "reason": "missing_in_A"})

    types = sorted(PROVISIONAL_TYPES)
    cm_path = out_dir / "confusion_matrix.csv"
    with cm_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["A\\B", *types])
        for ta in types:
            w.writerow([ta, *[confusion.get((ta, tb), 0) for tb in types]])

    # Minimal summary markdown (explicitly states match rule).
    summary_lines = [
        "# IAA summary",
        "",
        f"- match_rule: {args.match}",
        f"- total_A: {total_a}",
        f"- total_B: {total_b}",
        f"- matched_pairs: {matched}",
        f"- disagreements: {len([d for d in disagreements if d['reason'] != 'type_mismatch'])} (missing) + {len([d for d in disagreements if d['reason'] == 'type_mismatch'])} (type)",
        "",
        "Top confusions (A→B):",
    ]
    for (ta, tb), c in confusion.most_common(10):
        if ta != tb:
            summary_lines.append(f"- {ta} → {tb}: {c}")
    (out_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    from ner_ontology_utils import write_jsonl
    disagreements.sort(key=lambda d: (d["passage_urn"], d["reason"]))
    write_jsonl(out_dir / "disagreements.jsonl", disagreements)


if __name__ == "__main__":
    main()
