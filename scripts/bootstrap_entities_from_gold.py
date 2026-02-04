#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ner_ontology_utils import PROVISIONAL_TO_MVO, iter_jsonl, normalize_greek


TYPE_TO_FILE = {
    "PLACE": "places.tsv",
    "TOOL": "tools.tsv",
    "PROCESS": "processes.tsv",
    "PROPERTY": "properties.tsv",
    "MATERIAL": "materials.tsv",
    "MEASURE": "measures.tsv",
    "PERSON_GROUP": "person_groups.tsv",
}


def entity_id(mvo_type: str, preferred_norm: str) -> str:
    raw = f"{mvo_type}|{preferred_norm}".encode("utf-8")
    return "ent_" + mvo_type.lower() + "_" + hashlib.sha1(raw).hexdigest()[:12]


def main() -> None:
    ap = argparse.ArgumentParser(description="Bootstrap entity registries from gold mention JSONL.")
    ap.add_argument("--gold", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Always overwrite all expected registries so reruns don't leave stale categories.
    for fname in TYPE_TO_FILE.values():
        path = out_dir / fname
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f, fieldnames=["entity_id", "mvo_type", "preferred_label", "preferred_label_norm", "notes"], delimiter="\t"
            )
            w.writeheader()

    # Group by (mvo_type, surface_norm); pick most common surface as preferred label.
    buckets: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)

    for row in iter_jsonl(Path(args.gold)):
        ptype = str(row.get("provisional_type"))
        mvo_type = PROVISIONAL_TO_MVO.get(ptype)
        if not mvo_type:
            continue
        norm = str(row.get("surface_norm") or normalize_greek(str(row.get("surface") or "")))
        surface = str(row.get("surface") or "")
        if not norm or not surface:
            continue
        buckets[(mvo_type, norm)][surface] += 1

    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (mvo_type, norm), counter in buckets.items():
        preferred = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        eid = entity_id(mvo_type, norm)
        by_type[mvo_type].append(
            {
                "entity_id": eid,
                "mvo_type": mvo_type,
                "preferred_label": preferred,
                "preferred_label_norm": norm,
                "notes": "",
            }
        )

    for mvo_type, rows in by_type.items():
        fname = TYPE_TO_FILE[mvo_type]
        path = out_dir / fname
        rows.sort(key=lambda r: r["entity_id"])
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f, fieldnames=["entity_id", "mvo_type", "preferred_label", "preferred_label_norm", "notes"], delimiter="\t"
            )
            w.writeheader()
            for r in rows:
                w.writerow(r)


if __name__ == "__main__":
    main()
