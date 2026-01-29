#!/usr/bin/env python3
"""Validation scaffold."""

import os
from supabase import create_client

def main() -> None:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY.")
    client = create_client(url, key)
    resp = client.table("works").select("id").limit(1).execute()
    print("works smoke:", resp.data)

if __name__ == "__main__":
    main()
