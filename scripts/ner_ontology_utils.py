#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

NORMALIZER_VERSION = "greek_nfd_v1"
TOKENIZER_VERSION = "unicode_alnum_v1"

PROVISIONAL_TYPES = {
    "PLACE",
    "INSTRUMENT",
    "ACTION",
    "QUALITY",
    "MATERIAL",
    "MEASURE",
    "PERSON_GROUP",
}

PROVISIONAL_TO_MVO = {
    "PLACE": "PLACE",
    "INSTRUMENT": "TOOL",
    "ACTION": "PROCESS",
    "QUALITY": "PROPERTY",
    "MATERIAL": "MATERIAL",
    "MEASURE": "MEASURE",
    "PERSON_GROUP": "PERSON_GROUP",
}

MVO_TO_PROVISIONAL = {v: k for k, v in PROVISIONAL_TO_MVO.items()}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_greek(text: str) -> str:
    # Mirrors DB normalize_greek + app/src/lib/greek/normalize.ts:
    # NFD; U+0345 -> 'ι'; strip combining marks; lower.
    nfd = unicodedata.normalize("NFD", text or "")
    with_inline_iota = nfd.replace("\u0345", "ι")
    stripped = re.sub(r"[\u0300-\u036f]+", "", with_inline_iota)
    return stripped.lower()


def tokenize(text: str) -> list[str]:
    # Deterministic, conservative: group contiguous alnum as tokens.
    # Treat everything else (punctuation, symbols, whitespace) as separators.
    text_nfc = unicodedata.normalize("NFC", text or "")
    tokens: list[str] = []
    buf: list[str] = []
    for ch in text_nfc:
        if ch.isalnum():
            buf.append(ch)
            continue
        if buf:
            tokens.append("".join(buf))
            buf = []
    if buf:
        tokens.append("".join(buf))
    return tokens


def json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dumps(obj) + "\n", encoding="utf-8")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json_dumps(row) + "\n")


def localname(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def extract_text_with_breaks(elem: ET.Element) -> str:
    parts: list[str] = []

    def rec(node: ET.Element) -> None:
        if node.text:
            parts.append(node.text)
        for child in node:
            if localname(child.tag) in {"lb", "pb", "milestone"}:
                parts.append(" ")
            else:
                rec(child)
            if child.tail:
                parts.append(child.tail)

    rec(elem)
    text = "".join(parts)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_edition_div(root: ET.Element) -> ET.Element:
    divs = root.findall(".//tei:text/tei:body//tei:div[@type='edition']", TEI_NS)
    if not divs:
        raise ValueError("No tei:text/tei:body//tei:div[@type='edition'] found.")
    # Prefer the div with CTS-like @n (this file has it).
    for d in divs:
        n = d.get("n") or ""
        if "urn:cts:" in n:
            return d
    return divs[0]


def extract_work_urn(root: ET.Element) -> str:
    edition = find_edition_div(root)
    n = edition.get("n")
    if n and "urn:cts:" in n:
        return n.strip()
    # Fallback: scan idno values in header.
    for idno in root.findall(".//tei:teiHeader//tei:idno", TEI_NS):
        if idno.text and "urn:cts:" in idno.text:
            return idno.text.strip()
    raise ValueError("Could not extract work URN from TEI (no CTS urn found).")


@dataclass(frozen=True)
class Passage:
    passage_urn: str
    passage_ref: str
    token_start: int
    token_end: int
    tokens: list[str]
    tokens_norm: list[str]

def build_passages_from_edition(
    edition_div: ET.Element,
    work_urn: str,
    *,
    max_passages: int | None = None,
) -> list[Passage]:
    # ElementTree lacks parent pointers. We traverse the tree and maintain a stack.
    passages: list[Passage] = []
    token_cursor = 0
    counters: dict[tuple[str, ...], int] = {}

    def walk(node: ET.Element, textpart_stack: list[str]) -> None:
        nonlocal token_cursor
        if max_passages is not None and len(passages) >= max_passages:
            return

        if localname(node.tag) == "div" and node.get("type") == "textpart":
            n = (node.get("n") or "?").strip() or "?"
            textpart_stack.append(n)

        if localname(node.tag) == "p":
            if not textpart_stack:
                return
            text = extract_text_with_breaks(node)
            tokens = tokenize(text)
            if not tokens:
                return
            tokens_norm = [normalize_greek(t) for t in tokens]

            key = tuple(textpart_stack)
            counters[key] = counters.get(key, 0) + 1
            passage_ref = ".".join([*key, str(counters[key])])
            passage_urn = f"{work_urn}:{passage_ref}"

            token_start = token_cursor
            token_end = token_cursor + len(tokens)
            token_cursor = token_end

            passages.append(
                Passage(
                    passage_urn=passage_urn,
                    passage_ref=passage_ref,
                    token_start=token_start,
                    token_end=token_end,
                    tokens=tokens,
                    tokens_norm=tokens_norm,
                )
            )
            return

        for child in list(node):
            walk(child, textpart_stack)
            if max_passages is not None and len(passages) >= max_passages:
                break

        if localname(node.tag) == "div" and node.get("type") == "textpart":
            textpart_stack.pop()

    walk(edition_div, [])
    return passages
