#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import yaml


LEXICON_HEADERS = ["entity_id", "preferred_label", "variant", "variant_norm", "notes"]
ENTITY_HEADERS = ["entity_id", "mvo_type", "preferred_label", "preferred_label_norm", "notes"]


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping at top level")
    return data


def check_tsv_headers(path: Path, expected: list[str]) -> list[str]:
    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)
    if header is None:
        return [f"{path}: empty TSV"]
    if header != expected:
        return [f"{path}: header mismatch; expected {expected} got {header}"]
    return []


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate MVO + relations + entity/lexicon TSV schemas.")
    ap.add_argument("--mvo", required=True)
    ap.add_argument("--relations", required=True)
    ap.add_argument("--entities", help="Directory containing data/entities/*.tsv")
    ap.add_argument("--lexicons", help="Directory containing data/lexicons/*.tsv")
    args = ap.parse_args()

    errors: list[str] = []

    mvo = load_yaml(Path(args.mvo))
    rels = load_yaml(Path(args.relations))

    types = (mvo.get("types") or {})
    if not isinstance(types, dict) or not types:
        errors.append("mvo.yaml: missing or empty top-level 'types' mapping")
        type_names: set[str] = set()
    else:
        type_names = set(types.keys())

    relations = (rels.get("relations") or {})
    if not isinstance(relations, dict):
        errors.append("relations.yaml: missing or invalid top-level 'relations' mapping")
        relations = {}

    for rel_name, spec in relations.items():
        if not isinstance(spec, dict):
            errors.append(f"relations.yaml: relation {rel_name} must be a mapping")
            continue
        domain = spec.get("domain") or []
        rng = spec.get("range") or []
        if not isinstance(domain, list) or not isinstance(rng, list):
            errors.append(f"relations.yaml: relation {rel_name} domain/range must be lists")
            continue
        for t in domain:
            if t not in type_names:
                errors.append(f"relations.yaml: relation {rel_name} domain type not in MVO: {t}")
        for t in rng:
            if t not in type_names:
                errors.append(f"relations.yaml: relation {rel_name} range type not in MVO: {t}")

    if args.entities:
        ent_dir = Path(args.entities)
        for path in sorted(ent_dir.glob("*.tsv")):
            errors.extend(check_tsv_headers(path, ENTITY_HEADERS))

    if args.lexicons:
        lex_dir = Path(args.lexicons)
        for path in sorted(lex_dir.glob("*.tsv")):
            errors.extend(check_tsv_headers(path, LEXICON_HEADERS))

    if errors:
        raise SystemExit("Ontology validation failed:\n- " + "\n- ".join(errors))
    print("OK")


if __name__ == "__main__":
    main()

