#!/usr/bin/env python3
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

from ner_ontology_utils import (
    NORMALIZER_VERSION,
    TOKENIZER_VERSION,
    build_passages_from_edition,
    extract_work_urn,
    find_edition_div,
    sha256_file,
    write_json,
)


def main() -> None:
    ap = argparse.ArgumentParser(description="Build deterministic token index for one TEI work.")
    ap.add_argument("--tei-file", help="Path to a TEI XML file.")
    ap.add_argument("--tei", help="TEI directory (docs/wbs_ner_ontology.md compatibility).")
    ap.add_argument("--work", help="Work identifier used to locate TEI file in --tei (e.g., filename stem).")
    ap.add_argument("--work-slug", help="Stable work slug used in paths (defaults to --work).")
    ap.add_argument("--out", required=True, help="Output JSON path or directory (e.g., data/token_index).")
    ap.add_argument("--work-urn", help="Override extracted CTS work URN.")
    ap.add_argument("--max-passages", type=int, help="Optional limit for smoke runs.")
    args = ap.parse_args()

    tei_path: Path
    if args.tei_file:
        tei_path = Path(args.tei_file)
    elif args.tei and args.work:
        tei_path = Path(args.tei) / f"{args.work}.xml"
    else:
        raise SystemExit("Provide --tei-file OR (--tei and --work).")

    work_slug = (args.work_slug or args.work or tei_path.stem)

    out_path = Path(args.out)
    if out_path.exists() and out_path.is_dir():
        out_path = out_path / f"{work_slug}.json"
    elif str(out_path).endswith(("/", "\\")) or out_path.suffix.lower() != ".json":
        # Treat as directory path even if it doesn't exist yet.
        out_path = out_path / f"{work_slug}.json"

    tree = ET.parse(tei_path)
    root = tree.getroot()
    work_urn = (args.work_urn or extract_work_urn(root)).strip()

    edition = find_edition_div(root)
    passages = build_passages_from_edition(edition, work_urn, max_passages=args.max_passages)

    tokens: list[str] = []
    tokens_norm: list[str] = []
    for p in passages:
        tokens.extend(p.tokens)
        tokens_norm.extend(p.tokens_norm)

    payload = {
        "work_slug": work_slug,
        "work_urn": work_urn,
        "source_tei_file": str(tei_path),
        "tei_sha256": sha256_file(tei_path),
        "tokenizer_version": TOKENIZER_VERSION,
        "normalizer_version": NORMALIZER_VERSION,
        "tokens": tokens,
        "tokens_norm": tokens_norm,
        "passages": [
            {
                "passage_urn": p.passage_urn,
                "passage_ref": p.passage_ref,
                "token_start": p.token_start,
                "token_end": p.token_end,
            }
            for p in passages
        ],
    }

    write_json(out_path, payload)


if __name__ == "__main__":
    main()
