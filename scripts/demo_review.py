#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ner_ontology_utils import iter_jsonl, write_jsonl


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic demo reviewer (MVP smoke only).")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    reviewed: list[dict[str, Any]] = []
    for item in iter_jsonl(Path(args.inp)):
        row = item.get("row")
        if not row:
            continue
        out = dict(row)
        out["notes"] = (out.get("notes") or "") + "|REVIEWED_AUTO_MVP"
        reviewed.append(out)

    reviewed.sort(key=lambda r: (r["work_slug"], r["passage_urn"], r["token_start"], r["token_end"]))
    write_jsonl(Path(args.out), reviewed)


if __name__ == "__main__":
    main()

