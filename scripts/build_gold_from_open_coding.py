#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Any

from ner_ontology_utils import iter_jsonl, write_jsonl


FIXED_TS = "2000-01-01T00:00:00Z"


def certainty_rank(c: Any) -> int:
    if isinstance(c, (int, float)):
        return int(round(float(c) * 100))
    return {"low": 0, "med": 50, "high": 100}.get(str(c), 0)


def stable_gold_mention_id(work_slug: str, passage_urn: str, token_start: int, token_end: int) -> str:
    raw = f"{work_slug}|{passage_urn}|{token_start}|{token_end}".encode("utf-8")
    return "g_" + hashlib.sha1(raw).hexdigest()[:12]


def key_for(row: dict[str, Any]) -> tuple[str, int, int]:
    return (str(row["passage_urn"]), int(row["token_start"]), int(row["token_end"]))


def main() -> None:
    ap = argparse.ArgumentParser(description="Build full gold_v0.jsonl from open-coding A/B plus adjudicated queue items.")
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--adjudicated-queue", required=True, help="JSONL of adjudicated decisions for queued items.")
    ap.add_argument("--out", required=True, help="Gold JSONL output path.")
    ap.add_argument("--annotator-id", default="ADJUDICATOR_MERGE")
    args = ap.parse_args()

    a_rows = list(iter_jsonl(Path(args.a)))
    b_rows = list(iter_jsonl(Path(args.b)))
    adj_rows = list(iter_jsonl(Path(args.adjudicated_queue)))

    by_key_a: dict[tuple[str, int, int], list[dict[str, Any]]] = defaultdict(list)
    by_key_b: dict[tuple[str, int, int], list[dict[str, Any]]] = defaultdict(list)
    for r in a_rows:
        by_key_a[key_for(r)].append(r)
    for r in b_rows:
        by_key_b[key_for(r)].append(r)

    # Adjudicated decisions indexed by span key.
    by_key_adj: dict[tuple[str, int, int], dict[str, Any]] = {}
    for r in adj_rows:
        by_key_adj[key_for(r)] = r

    gold: list[dict[str, Any]] = []
    keys = sorted(set(by_key_a.keys()) | set(by_key_b.keys()))

    for k in keys:
        aa = sorted(by_key_a.get(k, []), key=lambda r: (-certainty_rank(r.get("certainty")), r.get("annotator_id", "")))
        bb = sorted(by_key_b.get(k, []), key=lambda r: (-certainty_rank(r.get("certainty")), r.get("annotator_id", "")))

        # If there is an adjudicated decision for this span, take it.
        if k in by_key_adj:
            chosen = dict(by_key_adj[k])
            chosen["annotator_id"] = args.annotator_id
            chosen["timestamp"] = FIXED_TS
            chosen["notes"] = (chosen.get("notes") or "") + "|ADJ_QUEUE_DECISION"
            gold.append(chosen)
            continue

        # If both A and B exist and agree on type and neither is low, accept as gold.
        if aa and bb:
            ra = aa[0]
            rb = bb[0]
            if str(ra.get("provisional_type")) == str(rb.get("provisional_type")) and certainty_rank(ra.get("certainty")) > 0 and certainty_rank(rb.get("certainty")) > 0:
                out = dict(ra)
                out["mention_id"] = stable_gold_mention_id(out["work_slug"], out["passage_urn"], int(out["token_start"]), int(out["token_end"]))
                out["annotator_id"] = args.annotator_id
                out["timestamp"] = FIXED_TS
                out["notes"] = (out.get("notes") or "") + "|AUTO_AGREED_AB"
                gold.append(out)
                continue

        # Otherwise choose the highest-certainty available row and mark as auto decision.
        candidates = aa[:1] + bb[:1]
        if not candidates:
            continue
        chosen = sorted(candidates, key=lambda r: (-certainty_rank(r.get("certainty")), str(r.get("annotator_id", ""))))[0]
        out = dict(chosen)
        out["mention_id"] = stable_gold_mention_id(out["work_slug"], out["passage_urn"], int(out["token_start"]), int(out["token_end"]))
        out["annotator_id"] = args.annotator_id
        out["timestamp"] = FIXED_TS
        out["notes"] = (out.get("notes") or "") + "|AUTO_TIEBREAK"
        gold.append(out)

    gold.sort(key=lambda r: (r["work_slug"], r["passage_urn"], int(r["token_start"]), int(r["token_end"])))
    write_jsonl(Path(args.out), gold)


if __name__ == "__main__":
    main()

