#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from ner_ontology_utils import iter_jsonl, write_jsonl


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate a review queue from auto-tagged annotations.")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--token-index", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--window", type=int, default=12)
    args = ap.parse_args()

    idx = json.loads(Path(args.token_index).read_text(encoding="utf-8"))
    tokens = idx.get("tokens") or []

    rows = list(iter_jsonl(Path(args.inp)))
    by_passage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_passage[str(r["passage_urn"])].append(r)

    queue: list[dict[str, Any]] = []
    for passage_urn, items in sorted(by_passage.items()):
        items.sort(key=lambda r: (r["token_start"], r["token_end"]))
        for i, r in enumerate(items):
            reasons: list[str] = []
            ts = int(r["token_start"])
            te = int(r["token_end"])

            # Overlap check with immediate neighbors (enough for MVP).
            if i > 0:
                prev = items[i - 1]
                if int(prev["token_end"]) > ts:
                    reasons.append("OVERLAP")
            if i + 1 < len(items):
                nxt = items[i + 1]
                if te > int(nxt["token_start"]):
                    reasons.append("OVERLAP")

            if str(r.get("link_confidence")) == "low" or str(r.get("certainty")) == "low":
                reasons.append("LOW_CONFIDENCE")

            if not reasons:
                continue

            lo = max(0, ts - args.window)
            hi = min(len(tokens), te + args.window)
            queue.append({"reason": reasons, "row": r, "evidence_window": tokens[lo:hi]})

    queue.sort(key=lambda q: (q["row"]["work_slug"], q["row"]["passage_urn"], q["row"]["token_start"]))
    write_jsonl(Path(args.out), queue)


if __name__ == "__main__":
    main()

