import Link from "next/link";
import { supabaseBrowser } from "@/lib/supabase/browser";

export default async function LemmataPage() {
  const supabase = supabaseBrowser();
  const { data, error } = await supabase
    .from("lemmata")
    .select("id, headword_gr, headword_en")
    .order("headword_gr", { ascending: true })
    .limit(200);

  return (
    <main style={{ padding: 24, maxWidth: 900 }}>
      <h1 style={{ marginTop: 0 }}>Lemmata</h1>
      {error && <pre>{String(error.message)}</pre>}
      <ul>
        {(data ?? []).map((l) => (
          <li key={l.id}>
            <Link href={`/lemmata/${l.id}`}>{l.headword_gr}</Link>
            {l.headword_en ? ` — ${l.headword_en}` : ""}
          </li>
        ))}
      </ul>
    </main>
  );
}
