#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from ner_ontology_utils import iter_jsonl, write_jsonl


def jaccard(a0: int, a1: int, b0: int, b1: int) -> float:
    inter = max(0, min(a1, b1) - max(a0, b0))
    union = (a1 - a0) + (b1 - b0) - inter
    return (inter / union) if union else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate adjudication queue from two open-coding JSONL files.")
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--token-index", required=True, help="Token index JSON for evidence windows.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--overlap-threshold", type=float, default=0.5)
    ap.add_argument("--window", type=int, default=12, help="Evidence window tokens on each side (approx).")
    args = ap.parse_args()

    token_index = json.loads(Path(args.token_index).read_text(encoding="utf-8"))
    tokens = token_index.get("tokens") or []

    a = list(iter_jsonl(Path(args.a)))
    b = list(iter_jsonl(Path(args.b)))

    by_passage_a: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_passage_b: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in a:
        by_passage_a[str(r["passage_urn"])].append(r)
    for r in b:
        by_passage_b[str(r["passage_urn"])].append(r)

    queue: list[dict[str, Any]] = []
    for passage_urn in sorted(set(by_passage_a) | set(by_passage_b)):
        aa = sorted(by_passage_a.get(passage_urn, []), key=lambda r: (r["token_start"], r["token_end"]))
        bb = sorted(by_passage_b.get(passage_urn, []), key=lambda r: (r["token_start"], r["token_end"]))
        used_b: set[int] = set()

        def ctx(ts: int, te: int) -> list[str]:
            lo = max(0, ts - args.window)
            hi = min(len(tokens), te + args.window)
            return tokens[lo:hi]

        for ra in aa:
            best_i = None
            best_s = 0.0
            for i, rb in enumerate(bb):
                if i in used_b:
                    continue
                s = jaccard(int(ra["token_start"]), int(ra["token_end"]), int(rb["token_start"]), int(rb["token_end"]))
                if s > best_s:
                    best_s, best_i = s, i
            rb = bb[best_i] if best_i is not None and best_s >= args.overlap_threshold else None
            if rb is not None:
                used_b.add(best_i)  # type: ignore[arg-type]

            needs_queue = rb is None
            if rb is not None:
                if str(ra.get("provisional_type")) != str(rb.get("provisional_type")):
                    needs_queue = True
                if str(ra.get("certainty")) == "low" or str(rb.get("certainty")) == "low":
                    needs_queue = True

            if not needs_queue:
                continue

            ts = int(ra["token_start"])
            te = int(ra["token_end"])
            row = {
                "work_urn": ra["work_urn"],
                "work_slug": ra["work_slug"],
                "passage_urn": passage_urn,
                "token_start": ts,
                "token_end": te,
                "surface": ra["surface"],
                "surface_norm": ra["surface_norm"],
                "a": ra,
                "b": rb,
                "evidence_window": ctx(ts, te),
            }
            queue.append(row)

        for i, rb in enumerate(bb):
            if i in used_b:
                continue
            ts = int(rb["token_start"])
            te = int(rb["token_end"])
            queue.append(
                {
                    "work_urn": rb["work_urn"],
                    "work_slug": rb["work_slug"],
                    "passage_urn": passage_urn,
                    "token_start": ts,
                    "token_end": te,
                    "surface": rb["surface"],
                    "surface_norm": rb["surface_norm"],
                    "a": None,
                    "b": rb,
                    "evidence_window": ctx(ts, te),
                }
            )

    queue.sort(key=lambda r: (r["work_slug"], r["passage_urn"], r["token_start"], r["token_end"]))
    write_jsonl(Path(args.out), queue)


if __name__ == "__main__":
    main()

