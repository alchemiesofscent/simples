#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from ner_ontology_utils import PROVISIONAL_TYPES, normalize_greek, write_jsonl


FIXED_TS = "2000-01-01T00:00:00Z"


def mention_id(work_slug: str, passage_urn: str, token_start: int, token_end: int, annotator_id: str) -> str:
    raw = f"{work_slug}|{passage_urn}|{token_start}|{token_end}|{annotator_id}".encode("utf-8")
    return "m_" + hashlib.sha1(raw).hexdigest()[:12]


def classify_token(tok: str, tok_norm: str, annotator_id: str) -> tuple[str, str, str]:
    # Returns (provisional_type, certainty, notes).
    tn = tok_norm or normalize_greek(tok)

    # Quick measure detection.
    if any(ch.isdigit() for ch in tok):
        return ("MEASURE", "med", "")
    if any(s in tn for s in ["δραχμ", "κοτυλ", "λιτρ", "μετρ", "ουγκ", "σταθμ"]):
        return ("MEASURE", "high", "")

    # Instruments/containers.
    if any(s in tn for s in ["αγγει", "σκευ", "κεραμ", "χαλκ", "υαλ", "κρυσταλλ", "κονδυλ"]):
        return ("INSTRUMENT", "med", "")

    # Actions/processes: prefer verb/infinitive stems; annotator differences for ambiguity.
    action_stems = ["θερμαιν", "ψυχει", "ξηραιν", "υγραιν", "καθαρ", "καθαιρ", "εμετ", "πταρμ", "βηχ", "τριβ", "μιγν", "ζε", "εψη", "κοπ", "λει", "κονι"]
    looks_verbal = tn.endswith("ειν") or tn.endswith("ει") or tn.endswith("εσθαι") or tn.endswith("ησαι")
    if any(s in tn for s in action_stems) and looks_verbal:
        return ("ACTION", "high", "")

    # Qualities/properties.
    quality_stems = ["θερμ", "ψυχρ", "ξηρ", "υγρ", "γλυκ", "πικρ", "αλμυρ", "οσμη", "χρωμ"]
    looks_property_noun = tn.endswith("της") or "τητα" in tn
    if any(s in tn for s in quality_stems) and (looks_property_noun or not looks_verbal):
        return ("QUALITY", "high", "")

    # Annotator B intentionally over-tags θερμ/ψυχρ as QUALITY even when verbal-looking.
    if annotator_id.upper().startswith("B") and any(s in tn for s in ["θερμ", "ψυχρ", "ξηρ", "υγρ"]):
        return ("QUALITY", "med", "HEURISTIC_B_PREFERS_QUALITY")

    # Materials: Galen SMT has many substance mentions.
    material_stems = [
        "φαρμακ",
        "υδωρ",
        "πυρεθρ",
        "καστορι",
        "υοσκυαμ",
        "μανδραγορ",
        "τροφ",
        "πυρ",
        "μελι",
        "οινος",
        "ελαι",
    ]
    if any(s in tn for s in material_stems):
        return ("MATERIAL", "high", "")

    # Fallback: keep empirical and conservative.
    return ("MATERIAL", "low", "HEURISTIC_DEFAULT_UNCERTAIN")


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic demo open-coding generator (MVP smoke only).")
    ap.add_argument("--manifest", required=True, help="data/samples/sample_manifest.json")
    ap.add_argument("--annotator-id", required=True, help="Annotator id (e.g., A or B).")
    ap.add_argument("--out", required=True, help="Output JSONL path.")
    ap.add_argument("--seed", type=int, default=0, help="Unused (kept for CLI compatibility).")
    ap.add_argument("--max-mentions-per-passage", type=int, default=3)
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))

    rows: list[dict[str, Any]] = []

    for item in manifest.get("items", []):
        tokens = item.get("tokens") or []
        tokens_norm = item.get("tokens_norm") or []
        if not tokens:
            continue

        chosen_idxs: list[int] = []
        for rel_idx, tok_norm in enumerate(tokens_norm[: len(tokens)]):
            if len(chosen_idxs) >= int(args.max_mentions_per_passage):
                break
            tn = tok_norm or normalize_greek(tokens[rel_idx])
            # Pick "interesting" tokens by heuristic triggers, plus allow some qualities/actions early.
            if any(s in tn for s in ["φαρμακ", "θερμ", "ψυχρ", "ξηρ", "υγρ", "υδωρ", "πυρεθρ", "καστορι", "υοσκυαμ", "μανδραγορ"]):
                chosen_idxs.append(rel_idx)
            elif any(s in tn for s in ["δραχμ", "κοτυλ", "μετρ"]):
                chosen_idxs.append(rel_idx)

        if not chosen_idxs:
            # Fallback: first token.
            chosen_idxs = [0]

        for rel_idx in sorted(set(chosen_idxs)):
            tok = tokens[rel_idx]
            tok_norm = tokens_norm[rel_idx] if rel_idx < len(tokens_norm) else normalize_greek(tok)
            ptype, certainty, notes = classify_token(tok, tok_norm, args.annotator_id)
            if ptype not in PROVISIONAL_TYPES:
                ptype, certainty, notes = ("MATERIAL", "low", "HEURISTIC_FALLBACK")

            token_start = int(item["token_start"]) + rel_idx
            token_end = token_start + 1
            mid = mention_id(item["work_slug"], item["passage_urn"], token_start, token_end, args.annotator_id)

            rows.append(
                {
                    "mention_id": mid,
                    "work_urn": item["work_urn"],
                    "passage_urn": item["passage_urn"],
                    "work_slug": item["work_slug"],
                    "token_start": token_start,
                    "token_end": token_end,
                    "surface": tok,
                    "surface_norm": tok_norm,
                    "provisional_type": ptype,
                    "certainty": certainty,
                    "annotator_id": args.annotator_id,
                    "timestamp": FIXED_TS,
                    "evidence_window": tokens[max(0, rel_idx - 5) : min(len(tokens), rel_idx + 6)],
                    "notes": notes,
                }
            )

    rows.sort(key=lambda r: (r["work_slug"], r["passage_urn"], r["token_start"], r["token_end"], r["annotator_id"]))
    write_jsonl(Path(args.out), rows)


if __name__ == "__main__":
    main()
