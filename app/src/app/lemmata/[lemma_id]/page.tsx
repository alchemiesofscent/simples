import { supabaseBrowser } from "@/lib/supabase/browser";

export default async function LemmaDetail({ params }: { params: { lemma_id: string } }) {
  const supabase = supabaseBrowser();

  const { data: lemma } = await supabase
    .from("lemmata")
    .select("id, headword_gr, headword_en")
    .eq("id", params.lemma_id)
    .maybeSingle();

  const { data: links, error } = await supabase
    .from("entry_lemmata")
    .select("is_primary, entries(id, loc, chapter_gr, entry_gr, translation_en, work_id)")
    .eq("lemma_id", params.lemma_id);

  const primary = (links ?? []).filter((x: any) => x.is_primary);
  const discussed = (links ?? []).filter((x: any) => !x.is_primary);

  return (
    <main style={{ padding: 24, maxWidth: 900 }}>
      <h1 style={{ marginTop: 0 }}>
        {lemma?.headword_gr ?? params.lemma_id}
        {lemma?.headword_en ? ` — ${lemma.headword_en}` : ""}
      </h1>

      {error && <pre>{String(error.message)}</pre>}

      <section style={{ marginTop: 24 }}>
        <h2>Primary entries</h2>
        {primary.map((x: any) => (
          <article key={x.entries.id} style={{ padding: 12, border: "1px solid #ddd", marginBottom: 12 }}>
            <div><strong>{x.entries.work_id}</strong> {x.entries.loc}</div>
            {x.entries.chapter_gr && <div>{x.entries.chapter_gr}</div>}
            {x.entries.entry_gr && <div style={{ marginTop: 8 }}>{x.entries.entry_gr}</div>}
            {x.entries.translation_en && <div style={{ marginTop: 8, opacity: 0.8 }}>{x.entries.translation_en}</div>}
          </article>
        ))}
        {primary.length === 0 && <p>(none yet)</p>}
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Also discussed</h2>
        {discussed.map((x: any) => (
          <article key={x.entries.id} style={{ padding: 12, border: "1px solid #ddd", marginBottom: 12, opacity: 0.9 }}>
            <div><strong>{x.entries.work_id}</strong> {x.entries.loc} <span style={{ fontSize: 12 }}>(discussed)</span></div>
            {x.entries.chapter_gr && <div>{x.entries.chapter_gr}</div>}
          </article>
        ))}
        {discussed.length === 0 && <p>(none yet)</p>}
      </section>
    </main>
  );
}
