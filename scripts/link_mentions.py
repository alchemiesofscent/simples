#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from ner_ontology_utils import MVO_TO_PROVISIONAL, PROVISIONAL_TO_MVO, iter_jsonl, write_jsonl


def load_lexicons(dir_path: Path) -> dict[str, dict[str, list[str]]]:
    # Returns: mvo_type -> variant_norm -> [entity_id...]
    mapping: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for path in sorted(dir_path.glob("*.tsv")):
        # Infer mvo_type from filename convention (places/tools/etc.).
        name = path.stem
        file_to_type = {
            "places": "PLACE",
            "tools": "TOOL",
            "processes": "PROCESS",
            "properties": "PROPERTY",
            "materials": "MATERIAL",
            "measures": "MEASURE",
            "person_groups": "PERSON_GROUP",
        }
        mvo_type = file_to_type.get(name)
        if not mvo_type:
            continue
        with path.open("r", encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                vn = (r.get("variant_norm") or "").strip()
                eid = (r.get("entity_id") or "").strip()
                if vn and eid:
                    mapping[mvo_type][vn].append(eid)
    return mapping


def main() -> None:
    ap = argparse.ArgumentParser(description="Link mention JSONL to entity IDs using lexicon TSVs.")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--lexicons", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--unlinked", required=True)
    args = ap.parse_args()

    lex = load_lexicons(Path(args.lexicons))

    linked: list[dict[str, Any]] = []
    unlinked: list[dict[str, Any]] = []

    for row in iter_jsonl(Path(args.inp)):
        ptype = str(row.get("provisional_type"))
        mvo_type = PROVISIONAL_TO_MVO.get(ptype)
        if not mvo_type:
            unlinked.append({"reason": "unknown_type", "row": row})
            continue
        vn = str(row.get("surface_norm") or "").strip()
        candidates = lex.get(mvo_type, {}).get(vn, [])
        if len(candidates) == 1:
            out = dict(row)
            out["mvo_type"] = mvo_type
            out["entity_id"] = candidates[0]
            out["link_method"] = "exact_norm"
            out["link_confidence"] = "high"
            out["provisional_type"] = ptype or MVO_TO_PROVISIONAL.get(mvo_type) or ptype
            linked.append(out)
        elif len(candidates) > 1:
            unlinked.append({"reason": "ambiguous", "mvo_type": mvo_type, "surface_norm": vn, "candidates": candidates, "row": row})
        else:
            unlinked.append({"reason": "no_match", "mvo_type": mvo_type, "surface_norm": vn, "row": row})

    linked.sort(key=lambda r: (r["work_slug"], r["passage_urn"], r["token_start"], r["token_end"]))
    unlinked.sort(key=lambda r: (r.get("reason", ""), r.get("mvo_type", ""), r.get("surface_norm", "")))
    write_jsonl(Path(args.out), linked)
    write_jsonl(Path(args.unlinked), unlinked)


if __name__ == "__main__":
    main()

