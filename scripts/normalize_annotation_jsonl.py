#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from ner_ontology_utils import iter_jsonl, normalize_greek, write_jsonl


def stable_mention_id(work_slug: str, passage_urn: str, token_start: int, token_end: int, annotator_id: str) -> str:
    raw = f"{work_slug}|{passage_urn}|{token_start}|{token_end}|{annotator_id}".encode("utf-8")
    return "m_" + hashlib.sha1(raw).hexdigest()[:12]


def main() -> None:
    ap = argparse.ArgumentParser(description="Normalize/repair annotation JSONL to match workflow invariants.")
    ap.add_argument("--token-index", required=True)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--recompute-mention-id", action="store_true", default=True)
    args = ap.parse_args()

    token_index = json.loads(Path(args.token_index).read_text(encoding="utf-8"))
    tokens: list[str] = token_index.get("tokens") or []

    out_rows: list[dict[str, Any]] = []
    for row in iter_jsonl(Path(args.inp)):
        r = dict(row)
        ts = int(r["token_start"])
        te = int(r["token_end"])
        notes = str(r.get("notes") or "")

        # Normalize certainty vocabulary.
        cert = r.get("certainty")
        if isinstance(cert, str):
            c = cert.strip().lower()
            if c == "medium":
                r["certainty"] = "med"
                notes = (notes + "|FIXED_CERTAINTY") if notes else "FIXED_CERTAINTY"
            elif c in {"low", "med", "high"}:
                r["certainty"] = c
            else:
                # Leave as-is; validator will catch.
                pass

        # Fix inclusive/invalid token_end.
        if te <= ts:
            te = ts + 1
            r["token_end"] = te
            notes = (notes + "|FIXED_TOKEN_END") if notes else "FIXED_TOKEN_END"

        # Fix surface/surface_norm if inconsistent with token index.
        if 0 <= ts < te <= len(tokens):
            expected_surface = " ".join(tokens[ts:te])
            if str(r.get("surface") or "") != expected_surface:
                r["surface"] = expected_surface
                notes = (notes + "|FIXED_SURFACE") if notes else "FIXED_SURFACE"

        surface = str(r.get("surface") or "")
        expected_norm = normalize_greek(surface)
        if str(r.get("surface_norm") or "") != expected_norm:
            r["surface_norm"] = expected_norm
            notes = (notes + "|FIXED_SURFACE_NORM") if notes else "FIXED_SURFACE_NORM"

        if args.recompute_mention_id:
            r["mention_id"] = stable_mention_id(str(r["work_slug"]), str(r["passage_urn"]), int(r["token_start"]), int(r["token_end"]), str(r["annotator_id"]))

        if notes:
            r["notes"] = notes

        out_rows.append(r)

    out_rows.sort(key=lambda x: (x.get("work_slug", ""), x.get("passage_urn", ""), int(x.get("token_start", 0)), int(x.get("token_end", 0))))
    write_jsonl(Path(args.out), out_rows)


if __name__ == "__main__":
    main()
