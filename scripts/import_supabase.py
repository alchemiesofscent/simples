#!/usr/bin/env python3
"""Import pipeline scaffold (idempotent upserts)."""

import os, csv
from typing import Dict, Any, List
from supabase import create_client, Client

def get_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY.")
    return create_client(url, key)

def read_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def upsert(client: Client, table: str, rows: List[Dict[str, Any]], on_conflict: str) -> None:
    if rows:
        client.table(table).upsert(rows, on_conflict=on_conflict).execute()

def main() -> None:
    client = get_client()
    print("TODO: wire CSVs under data-workbench/out/ and upsert in dependency order.")

if __name__ == "__main__":
    main()
