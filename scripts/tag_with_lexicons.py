#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from ner_ontology_utils import MVO_TO_PROVISIONAL, normalize_greek, tokenize, write_jsonl


FIXED_TS = "2000-01-01T00:00:00Z"


def load_lexicon_phrases(dir_path: Path, max_ngram: int) -> dict[tuple[str, ...], list[tuple[str, str]]]:
    # Returns token_norm tuple -> [(entity_id, mvo_type)...]
    file_to_type = {
        "places": "PLACE",
        "tools": "TOOL",
        "processes": "PROCESS",
        "properties": "PROPERTY",
        "materials": "MATERIAL",
        "measures": "MEASURE",
        "person_groups": "PERSON_GROUP",
    }
    phrases: dict[tuple[str, ...], list[tuple[str, str]]] = defaultdict(list)
    for path in sorted(dir_path.glob("*.tsv")):
        mvo_type = file_to_type.get(path.stem)
        if not mvo_type:
            continue
        with path.open("r", encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                eid = (r.get("entity_id") or "").strip()
                variant = (r.get("variant") or "").strip()
                if not eid or not variant:
                    continue
                toks = tokenize(variant)
                toks_norm = tuple(normalize_greek(t) for t in toks if t)
                if not toks_norm or len(toks_norm) > max_ngram:
                    continue
                phrases[toks_norm].append((eid, mvo_type))
    return phrases


def main() -> None:
    ap = argparse.ArgumentParser(description="Precision-first lexicon tagging using token_index JSON.")
    ap.add_argument("--tei", help="TEI directory (accepted for docs compatibility; not used).")
    ap.add_argument("--work", help="Work slug/stem to infer token index path (docs compatibility).")
    ap.add_argument("--token-index", help="Token index JSON path.")
    ap.add_argument("--token-index-dir", default="data/token_index", help="Directory to infer token index from when using --work.")
    ap.add_argument("--lexicons", required=True)
    ap.add_argument("--out", required=True, help="Output JSONL path or directory.")
    ap.add_argument("--report", help="Coverage report markdown path (defaults to reports/coverage/{workSlug}.md).")
    ap.add_argument("--max-ngram", type=int, default=5)
    ap.add_argument("--annotator-id", default="AUTO_LEXICON")
    args = ap.parse_args()

    token_index_path: Path
    if args.token_index:
        token_index_path = Path(args.token_index)
    elif args.work:
        token_index_path = Path(args.token_index_dir) / f"{args.work}.json"
    else:
        raise SystemExit("Provide --token-index OR --work (to infer from --token-index-dir).")

    idx = json.loads(token_index_path.read_text(encoding="utf-8"))
    work_slug = idx["work_slug"]
    work_urn = idx["work_urn"]
    tokens = idx.get("tokens") or []
    tokens_norm = idx.get("tokens_norm") or []
    passages = idx.get("passages") or []

    phrases = load_lexicon_phrases(Path(args.lexicons), args.max_ngram)

    out_rows: list[dict[str, Any]] = []
    counts_by_type: dict[str, int] = defaultdict(int)
    ambiguous = 0

    for p in passages:
        ts = int(p["token_start"])
        te = int(p["token_end"])
        p_tokens = tokens[ts:te]
        p_norm = tokens_norm[ts:te]
        passage_urn = p["passage_urn"]

        i = 0
        while i < len(p_norm):
            advanced = False
            for n in range(min(args.max_ngram, len(p_norm) - i), 0, -1):
                key = tuple(p_norm[i : i + n])
                cand = phrases.get(key)
                if not cand:
                    continue
                if len(cand) != 1:
                    ambiguous += 1
                    i += 1  # precision-first: skip, but always advance
                    advanced = True
                    break
                eid, mvo_type = cand[0]
                surf_tokens = p_tokens[i : i + n]
                surface = " ".join(surf_tokens)
                surface_norm = normalize_greek(surface)
                global_start = ts + i
                global_end = global_start + n
                out_rows.append(
                    {
                        "work_urn": work_urn,
                        "passage_urn": passage_urn,
                        "work_slug": work_slug,
                        "token_start": global_start,
                        "token_end": global_end,
                        "surface": surface,
                        "surface_norm": surface_norm,
                        "provisional_type": MVO_TO_PROVISIONAL.get(mvo_type, "MATERIAL"),
                        "mvo_type": mvo_type,
                        "certainty": "med",
                        "annotator_id": args.annotator_id,
                        "timestamp": FIXED_TS,
                        "entity_id": eid,
                        "link_method": "variant_norm",
                        "link_confidence": "med",
                        "evidence_window": p_tokens[max(0, i - 5) : min(len(p_tokens), i + n + 6)],
                    }
                )
                counts_by_type[mvo_type] += 1
                i += n
                advanced = True
                break
            if not advanced:
                i += 1

    out_rows.sort(key=lambda r: (r["work_slug"], r["passage_urn"], r["token_start"], r["token_end"], r["mvo_type"]))

    out_path = Path(args.out)
    if out_path.exists() and out_path.is_dir():
        out_path = out_path / f"auto_{work_slug}.jsonl"
    elif str(out_path).endswith(("/", "\\")) or out_path.suffix.lower() != ".jsonl":
        out_path = out_path / f"auto_{work_slug}.jsonl"
    write_jsonl(out_path, out_rows)

    report_lines = [
        f"# Coverage report: {work_slug}",
        "",
        f"- total_mentions: {len(out_rows)}",
        f"- ambiguous_skipped: {ambiguous}",
        "",
        "Mentions by type:",
    ]
    for t in sorted(counts_by_type):
        report_lines.append(f"- {t}: {counts_by_type[t]}")
    report_path = Path(args.report) if args.report else Path("reports/coverage") / f"{work_slug}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
