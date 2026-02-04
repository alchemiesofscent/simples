#!/usr/bin/env python3
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from ner_ontology_utils import TEI_NS, iter_jsonl


XML_NS = "http://www.w3.org/XML/1998/namespace"


def tei(tag: str) -> str:
    return f"{{{TEI_NS['tei']}}}{tag}"


def main() -> None:
    ap = argparse.ArgumentParser(description="Export TEI with standOff annotations from linked mention JSONL.")
    ap.add_argument("--tei-file", help="Input TEI XML file.")
    ap.add_argument("--tei", help="TEI directory (docs compatibility).")
    ap.add_argument("--work", help="Work stem to locate TEI file in --tei (docs compatibility).")
    ap.add_argument("--ann", required=True, help="Linked/reviewed JSONL.")
    ap.add_argument("--out", required=True, help="Output TEI path or directory.")
    args = ap.parse_args()

    tei_path: Path
    if args.tei_file:
        tei_path = Path(args.tei_file)
    elif args.tei and args.work:
        tei_path = Path(args.tei) / f"{args.work}.xml"
    else:
        raise SystemExit("Provide --tei-file OR (--tei and --work).")

    out_path = Path(args.out)
    if out_path.exists() and out_path.is_dir():
        out_path = out_path / tei_path.name
    elif str(out_path).endswith(("/", "\\")) or out_path.suffix.lower() != ".xml":
        out_path = out_path / tei_path.name

    tree = ET.parse(tei_path)
    root = tree.getroot()

    # Remove any existing standOff we may have produced in a previous run (idempotent).
    for existing in list(root.findall("tei:standOff", TEI_NS)):
        root.remove(existing)

    stand_off = ET.Element(tei("standOff"))
    list_ann = ET.SubElement(stand_off, tei("listAnnotation"))

    rows = list(iter_jsonl(Path(args.ann)))
    rows.sort(key=lambda r: (r.get("passage_urn", ""), int(r.get("token_start", 0)), int(r.get("token_end", 0))))

    for r in rows:
        mid = str(r.get("mention_id") or f"m_{r['token_start']}_{r['token_end']}")
        ann = ET.SubElement(list_ann, tei("annotation"))
        ann.set(f"{{{XML_NS}}}id", mid)
        ann.set("type", str(r.get("mvo_type") or r.get("provisional_type") or ""))
        ann.set("corresp", str(r.get("passage_urn") or ""))

        ptr = ET.SubElement(ann, tei("ptr"))
        ptr.set("target", f"{r['passage_urn']}#tok={r['token_start']}-{r['token_end']}")

        note = ET.SubElement(ann, tei("note"))
        note.text = f"entity_id={r.get('entity_id','')} surface={r.get('surface','')}"

    root.insert(1, stand_off)  # after teiHeader in typical TEI layouts
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(out_path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
