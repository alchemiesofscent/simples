#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ner_ontology_utils import write_jsonl, iter_jsonl


FIXED_TS = "2000-01-01T00:00:00Z"


def certainty_rank(c: str) -> int:
    return {"low": 0, "med": 1, "high": 2}.get(str(c), 0)


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic demo adjudication (MVP smoke only).")
    ap.add_argument("--in", dest="inp", required=True, help="Adjudication queue JSONL.")
    ap.add_argument("--out", required=True, help="Gold JSONL output.")
    ap.add_argument("--annotator-id", default="ADJUDICATOR_AUTO")
    args = ap.parse_args()

    gold: list[dict[str, Any]] = []
    for row in iter_jsonl(Path(args.inp)):
        a = row.get("a")
        b = row.get("b")
        base = a or b
        if base is None:
            continue

        chosen = base
        if a is not None and b is not None:
            if str(a.get("provisional_type")) == str(b.get("provisional_type")):
                chosen = a
            else:
                ca = certainty_rank(str(a.get("certainty")))
                cb = certainty_rank(str(b.get("certainty")))
                chosen = a if ca >= cb else b

        out = {
            "mention_id": chosen.get("mention_id"),
            "work_urn": chosen["work_urn"],
            "passage_urn": chosen["passage_urn"],
            "work_slug": chosen["work_slug"],
            "token_start": int(chosen["token_start"]),
            "token_end": int(chosen["token_end"]),
            "surface": chosen["surface"],
            "surface_norm": chosen["surface_norm"],
            "provisional_type": chosen["provisional_type"],
            "certainty": chosen.get("certainty", "low"),
            "annotator_id": args.annotator_id,
            "timestamp": FIXED_TS,
            "notes": "AUTO_ADJUDICATED_MVP",
            "evidence_window": row.get("evidence_window"),
        }
        gold.append(out)

    gold.sort(key=lambda r: (r["work_slug"], r["passage_urn"], r["token_start"], r["token_end"]))
    write_jsonl(Path(args.out), gold)


if __name__ == "__main__":
    main()

