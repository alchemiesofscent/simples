#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ner_ontology_utils import PROVISIONAL_TYPES, iter_jsonl, normalize_greek


CERTAINTY_ALLOWED = {"low", "med", "high"}


def is_numeric_certainty(value: Any) -> bool:
    try:
        f = float(value)
    except Exception:
        return False
    return 0.0 <= f <= 1.0


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate outputs against docs/ontology_coding_guidelines.md constraints.")
    ap.add_argument("--jsonl", nargs="+", required=True, help="One or more annotation JSONL files.")
    ap.add_argument("--phase", choices=["open_coding", "gold"], default="open_coding")
    ap.add_argument("--strict", action="store_true", help="Treat guideline warnings as errors.")
    args = ap.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    for path_str in args.jsonl:
        path = Path(path_str)
        for line_no, row in enumerate(iter_jsonl(path), start=1):
            ptype = str(row.get("provisional_type") or "")
            if ptype not in PROVISIONAL_TYPES:
                errors.append(f"{path}:{line_no}: illegal provisional_type={ptype!r}")

            certainty = row.get("certainty")
            if isinstance(certainty, str):
                if certainty not in CERTAINTY_ALLOWED:
                    errors.append(f"{path}:{line_no}: illegal certainty={certainty!r} (expected low|med|high or 0..1)")
            else:
                if not is_numeric_certainty(certainty):
                    errors.append(f"{path}:{line_no}: illegal certainty={certainty!r} (expected low|med|high or 0..1)")

            surface = str(row.get("surface") or "")
            surface_norm = str(row.get("surface_norm") or "")
            expected_norm = normalize_greek(surface)
            if surface_norm != expected_norm:
                errors.append(f"{path}:{line_no}: surface_norm mismatch (got {surface_norm!r}, expected {expected_norm!r})")

            if args.phase in {"open_coding", "gold"}:
                rels = row.get("relations")
                if rels:
                    warnings.append(f"{path}:{line_no}: relations present in {args.phase} (guidelines: avoid unless trivial)")

            if isinstance(certainty, str) and certainty == "low":
                notes = str(row.get("notes") or "").strip()
                if not notes:
                    msg = f"{path}:{line_no}: certainty=low but notes missing/empty (guidelines: add brief note)"
                    if args.strict:
                        errors.append(msg)
                    else:
                        warnings.append(msg)

    if warnings:
        print("WARN:")
        for w in warnings:
            print(f"- {w}")

    if errors:
        raise SystemExit("FAIL:\n- " + "\n- ".join(errors))
    print("OK")


if __name__ == "__main__":
    main()

