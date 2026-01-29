# simples (Ancient Simples)

Starter repo scaffold aligned to the MVP spec (v1.0.3+).

## Layout
- `docs/` — PRD/tech review/specs
- `supabase/` — local config + migrations
- `scripts/` — import + validation
- `app/` — Next.js alignment viewer/editor
- `data-workbench/` — staging (CSV scratch)

## Quickstart (local dev)
Prereqs: Node 20+, Python 3.11+, Supabase CLI

1) Install app deps
- `cd app && npm install`

2) Configure env
- copy `app/.env.local.example` → `app/.env.local`
- set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- for scripts (local only): set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`

3) Start local Supabase + migrate
- `cd supabase`
- `supabase start`
- `supabase db reset`

4) Run the web app
- `cd ../app`
- `npm run dev`
