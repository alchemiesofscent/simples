#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from ner_ontology_utils import json_dumps, write_json


def load_token_index(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def passage_book_key(passage_ref: str) -> str:
    # For Galen SMT, passage_ref begins with book n (e.g., "1.1.1").
    return (passage_ref.split(".", 1)[0] if passage_ref else "?") or "?"


def main() -> None:
    ap = argparse.ArgumentParser(description="Create a deterministic sample manifest from token_index JSON.")
    ap.add_argument(
        "--token-index",
        nargs="+",
        required=True,
        help="One or more token_index JSON paths or a directory path (docs/wbs_ner_ontology.md compatibility).",
    )
    ap.add_argument("--works", nargs="*", help="When --token-index is a directory, optional list of work slugs/stems.")
    ap.add_argument("--out", required=True, help="Output manifest path (JSON).")
    ap.add_argument("--n-passages", type=int, default=25, help="Total passages to sample.")
    ap.add_argument("--seed", type=int, default=0, help="Random seed.")
    ap.add_argument(
        "--max-passage-tokens",
        type=int,
        default=400,
        help="Skip passages longer than this (keeps LLM/human annotation practical).",
    )
    args = ap.parse_args()

    rng = random.Random(args.seed)
    out_path = Path(args.out)

    token_index_paths: list[Path] = []
    for raw in [Path(x) for x in args.token_index]:
        if raw.is_dir() or str(raw).endswith(("/", "\\")):
            if args.works:
                token_index_paths.extend([raw / f"{w}.json" for w in args.works])
            else:
                token_index_paths.extend(sorted(raw.glob("*.json")))
        else:
            token_index_paths.append(raw)

    items: list[dict[str, Any]] = []
    for p in token_index_paths:
        idx = load_token_index(p)
        passages = idx.get("passages") or []
        tokens = idx.get("tokens") or []
        tokens_norm = idx.get("tokens_norm") or []

        # Group by first passage_ref segment ("book") for light stratification.
        groups: dict[str, list[dict[str, Any]]] = {}
        for rec in passages:
            key = passage_book_key(rec.get("passage_ref", ""))
            ts = int(rec["token_start"])
            te = int(rec["token_end"])
            if (te - ts) > int(args.max_passage_tokens):
                continue
            groups.setdefault(key, []).append(rec)

        for g in groups.values():
            g.sort(key=lambda r: (r.get("passage_urn", ""), r.get("token_start", 0)))

        # Round-robin draw from shuffled groups to ensure coverage.
        group_keys = list(groups.keys())
        rng.shuffle(group_keys)
        chosen: list[dict[str, Any]] = []
        while group_keys and len(chosen) < int(args.n_passages):
            new_group_keys: list[str] = []
            for k in group_keys:
                if len(chosen) >= int(args.n_passages):
                    break
                if groups[k]:
                    chosen.append(groups[k].pop(0))
                    if groups[k]:
                        new_group_keys.append(k)
            group_keys = new_group_keys

        for rec in chosen:
            ts = int(rec["token_start"])
            te = int(rec["token_end"])
            passage_tokens = tokens[ts:te]
            passage_tokens_norm = tokens_norm[ts:te]
            tokens_with_offsets = [f"{ts + i}:{tok}" for i, tok in enumerate(passage_tokens)]
            items.append(
                {
                    "work_slug": idx["work_slug"],
                    "work_urn": idx["work_urn"],
                    "passage_urn": rec["passage_urn"],
                    "passage_ref": rec.get("passage_ref"),
                    # Passage bounds in WORK-GLOBAL token offsets.
                    "token_start": ts,
                    "token_end": te,
                    # Aliases to avoid confusion with mention token_start/token_end.
                    "passage_token_start": ts,
                    "passage_token_end": te,
                    "tokens": passage_tokens,
                    "tokens_norm": passage_tokens_norm,
                    "tokens_with_offsets": tokens_with_offsets,
                    "text": " ".join(passage_tokens),
                }
            )

    manifest = {
        "manifest_version": 1,
        "seed": args.seed,
        "n_passages": args.n_passages,
        "items": sorted(items, key=lambda r: (r["work_slug"], r["passage_urn"])),
    }

    # Use shared deterministic JSON writer.
    write_json(out_path, manifest)


if __name__ == "__main__":
    main()
