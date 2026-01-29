-- 001_init.sql — MVP schema baseline
begin;

create extension if not exists unaccent;
create extension if not exists pgcrypto;

-- Greek normalization:
-- NFD; U+0345 (COMBINING GREEK YPOGEGRAMMENI) -> 'ι'; unaccent; lower.
create or replace function public.normalize_greek(input text)
returns text
language sql
immutable
as $$
  select lower(
    unaccent(
      replace(
        normalize(coalesce(input,''), NFD),
        U&'\0345',
        'ι'
      )
    )
  );
$$;

create table if not exists public.works (
  id text primary key,
  urn text unique,
  title text not null,
  short_title text,
  author text,
  language text default 'grc',
  created_at timestamptz default now()
);

create table if not exists public.lemmata (
  id text primary key,
  urn text unique,
  headword_gr text not null,
  headword_gr_normalized text generated always as (public.normalize_greek(headword_gr)) stored,
  headword_en text,
  lemma_type text default 'simple',
  created_at timestamptz default now()
);

create table if not exists public.entries (
  id text primary key,
  urn text unique,
  work_id text not null references public.works(id) on delete restrict,
  loc text not null,
  chapter_gr text,
  lemma_gr text,
  entry_gr text,
  entry_gr_normalized text generated always as (public.normalize_greek(entry_gr)) stored,
  translation_en text,
  created_at timestamptz default now()
);

create table if not exists public.entry_lemmata (
  entry_id text not null references public.entries(id) on delete cascade,
  lemma_id text not null references public.lemmata(id) on delete cascade,
  is_primary boolean not null default false,
  created_at timestamptz default now(),
  primary key (entry_id, lemma_id)
);

create unique index if not exists ux_entry_lemmata_primary
  on public.entry_lemmata(entry_id)
  where is_primary = true;

create table if not exists public.editions (
  id text primary key,
  work_id text not null references public.works(id) on delete cascade,
  label text not null,
  citation text,
  is_default boolean not null default false,
  created_at timestamptz default now()
);

create unique index if not exists ux_editions_default_per_work
  on public.editions(work_id)
  where is_default = true;

create table if not exists public.entry_refs (
  id bigserial primary key,
  entry_id text not null references public.entries(id) on delete cascade,
  edition_id text not null references public.editions(id) on delete cascade,
  ref_kind text not null,
  vol text,
  start_n text,
  end_n text,
  ref_text text,
  created_at timestamptz default now()
);

create index if not exists idx_entry_refs_entry_id on public.entry_refs(entry_id);
create index if not exists idx_entry_refs_edition_id on public.entry_refs(edition_id);
create index if not exists idx_entry_refs_entry_edition on public.entry_refs(entry_id, edition_id);

create table if not exists public.suggested_lemmata_review (
  id bigserial primary key,
  entry_id text not null references public.entries(id) on delete cascade,
  lemma_id text not null references public.lemmata(id) on delete cascade,
  match_context text,
  confidence text,
  status text not null default 'pending',
  decided_by text,
  decided_at timestamptz,
  created_at timestamptz default now()
);

create index if not exists idx_suggested_lemmata_review_entry on public.suggested_lemmata_review(entry_id);
create index if not exists idx_suggested_lemmata_review_status on public.suggested_lemmata_review(status);

create table if not exists public.entry_notes (
  id bigserial primary key,
  entry_id text not null references public.entries(id) on delete cascade,
  note text not null,
  anchor text,
  created_by text,
  created_at timestamptz default now()
);

create table if not exists public.translation_versions (
  id bigserial primary key,
  entry_id text not null references public.entries(id) on delete cascade,
  translation_en text not null,
  status text not null default 'draft',
  created_by text,
  created_at timestamptz default now()
);

-- Non-redundant pharmacology: single source of truth in property_terms
create table if not exists public.property_terms (
  id text primary key,
  property_type text not null,
  canonical_gr text,
  canonical_en text,
  category text,
  tag text,
  parent_id text references public.property_terms(id) on delete set null,
  created_at timestamptz default now()
);

create index if not exists idx_property_terms_type on public.property_terms(property_type);

create table if not exists public.property_assertions (
  id bigserial primary key,
  entry_id text not null references public.entries(id) on delete cascade,
  property_type text not null,
  property_term_id text references public.property_terms(id) on delete restrict,
  evidence_text text not null,
  scope_part_id text,
  scope_prep_id text,
  confidence text,
  created_by text,
  created_at timestamptz default now()
);

create index if not exists idx_property_assertions_entry on public.property_assertions(entry_id);
create index if not exists idx_property_assertions_term on public.property_assertions(property_term_id);

commit;
