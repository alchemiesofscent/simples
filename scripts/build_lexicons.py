#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from ner_ontology_utils import normalize_greek


def main() -> None:
    ap = argparse.ArgumentParser(description="Build lexicon TSVs from entity registry TSVs.")
    ap.add_argument("--entities", required=True, help="Directory containing data/entities/*.tsv")
    ap.add_argument("--out-dir", required=True, help="Output directory (data/lexicons)")
    args = ap.parse_args()

    entities_dir = Path(args.entities)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Always overwrite all expected lexicons so reruns don't leave stale categories.
    expected = [
        "places.tsv",
        "tools.tsv",
        "processes.tsv",
        "properties.tsv",
        "materials.tsv",
        "measures.tsv",
        "person_groups.tsv",
    ]
    for fname in expected:
        path = out_dir / fname
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f, fieldnames=["entity_id", "preferred_label", "variant", "variant_norm", "notes"], delimiter="\t"
            )
            w.writeheader()

    for ent_path in sorted(entities_dir.glob("*.tsv")):
        out_path = out_dir / ent_path.name
        with ent_path.open("r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))

        lex_rows = []
        for r in rows:
            preferred = r.get("preferred_label") or ""
            variant = preferred
            lex_rows.append(
                {
                    "entity_id": r.get("entity_id") or "",
                    "preferred_label": preferred,
                    "variant": variant,
                    "variant_norm": normalize_greek(variant),
                    "notes": r.get("notes") or "",
                }
            )

        lex_rows.sort(key=lambda r: (r["entity_id"], r["variant_norm"], r["variant"]))
        with out_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["entity_id", "preferred_label", "variant", "variant_norm", "notes"], delimiter="\t")
            w.writeheader()
            for r in lex_rows:
                w.writerow(r)


if __name__ == "__main__":
    main()
