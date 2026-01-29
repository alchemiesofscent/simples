import Link from "next/link";

export default function Home() {
  return (
    <main style={{ padding: 24, maxWidth: 900 }}>
      <h1 style={{ marginTop: 0 }}>simples (Ancient Simples)</h1>
      <ul>
        <li><Link href="/lemmata">Browse lemmata</Link></li>
      </ul>
    </main>
  );
}
