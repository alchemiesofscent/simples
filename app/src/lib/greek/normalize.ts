// UI-side normalization consistent with DB normalize_greek.
// Rule: NFD; U+0345 -> 'ι'; strip combining marks; lower.
export function normalizeGreek(input: string): string {
  const nfd = (input ?? "").normalize("NFD");
  const withInlineIota = nfd.replace(/\u0345/g, "ι");
  const stripped = withInlineIota.replace(/[\u0300-\u036f]/g, "");
  return stripped.toLowerCase();
}
