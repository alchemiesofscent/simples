#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from ner_ontology_utils import PROVISIONAL_TYPES, normalize_greek, iter_jsonl


REQUIRED_FIELDS = {
    "work_urn",
    "passage_urn",
    "work_slug",
    "token_start",
    "token_end",
    "surface",
    "surface_norm",
    "provisional_type",
    "certainty",
    "annotator_id",
    "timestamp",
}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping at top level")
    return data


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate annotation JSONL schema + MVO conformity + token bounds.")
    ap.add_argument("--mvo", required=True)
    ap.add_argument("--relations", required=True)
    ap.add_argument("--token-index", required=True)
    ap.add_argument("--ann", required=True)
    ap.add_argument("--strict-surface", action="store_true")
    args = ap.parse_args()

    mvo = load_yaml(Path(args.mvo))
    rels = load_yaml(Path(args.relations))
    mvo_types = set((mvo.get("types") or {}).keys())
    rel_names = set((rels.get("relations") or {}).keys())

    idx = json.loads(Path(args.token_index).read_text(encoding="utf-8"))
    tokens = idx.get("tokens") or []
    work_slug = idx.get("work_slug")
    passage_map = {p["passage_urn"]: (int(p["token_start"]), int(p["token_end"])) for p in (idx.get("passages") or [])}

    errors: list[str] = []

    for i, row in enumerate(iter_jsonl(Path(args.ann)), start=1):
        missing = sorted(REQUIRED_FIELDS - set(row.keys()))
        if missing:
            errors.append(f"line {i}: missing fields: {missing}")
            continue

        if row.get("work_slug") != work_slug:
            errors.append(f"line {i}: work_slug {row.get('work_slug')} != token_index work_slug {work_slug}")

        ts = int(row["token_start"])
        te = int(row["token_end"])
        if not (0 <= ts < te <= len(tokens)):
            errors.append(f"line {i}: token span out of bounds: {ts}-{te} (len={len(tokens)})")

        pur = row.get("passage_urn")
        if pur in passage_map:
            ps, pe = passage_map[pur]
            if not (ps <= ts and te <= pe):
                errors.append(f"line {i}: span {ts}-{te} not within passage range {ps}-{pe} for {pur}")
        else:
            errors.append(f"line {i}: passage_urn not found in token index: {pur}")

        ptype = str(row.get("provisional_type"))
        if ptype not in PROVISIONAL_TYPES:
            errors.append(f"line {i}: illegal provisional_type: {ptype}")

        if "mvo_type" in row:
            mvo_type = str(row.get("mvo_type"))
            if mvo_type not in mvo_types:
                errors.append(f"line {i}: illegal mvo_type: {mvo_type}")

        sn = str(row.get("surface_norm") or "")
        expected = normalize_greek(str(row.get("surface") or ""))
        if sn != expected:
            errors.append(f"line {i}: surface_norm mismatch (got {sn!r}, expected {expected!r})")

        if args.strict_surface:
            expected_surface = " ".join(tokens[ts:te])
            if str(row.get("surface")) != expected_surface:
                errors.append(f"line {i}: surface mismatch (got {row.get('surface')!r}, expected {expected_surface!r})")

        rel_objs = row.get("relations")
        if rel_objs is not None:
            if not isinstance(rel_objs, list):
                errors.append(f"line {i}: relations must be a list")
            else:
                for rj in rel_objs:
                    if not isinstance(rj, dict):
                        errors.append(f"line {i}: relation object must be dict")
                        continue
                    rel = str(rj.get("rel") or "")
                    if rel and rel not in rel_names:
                        errors.append(f"line {i}: unknown relation rel={rel}")

    if errors:
        raise SystemExit("Annotation validation failed:\n- " + "\n- ".join(errors))
    print("OK")


if __name__ == "__main__":
    main()

