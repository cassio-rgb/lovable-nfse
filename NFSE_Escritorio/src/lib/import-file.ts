import { parseCSV } from "./imports";

function cellToString(v: unknown): string {
  if (v == null) return "";
  if (v instanceof Date) return `${v.getUTCFullYear()}-${String(v.getUTCMonth() + 1).padStart(2, "0")}`;
  return String(v);
}

export async function lerArquivo(f: File): Promise<string[][]> {
  if (/\.csv$/i.test(f.name)) return parseCSV(await f.text());
  if (/\.xlsx$/i.test(f.name)) {
    const mod = await import("read-excel-file/browser");
    const res: unknown = await mod.default(f);
    const rows = (Array.isArray(res) && res.length && !Array.isArray(res[0]) && (res[0] as { data?: unknown[][] }).data
      ? (res[0] as { data: unknown[][] }).data
      : (res as unknown[][]));
    return rows.map((r) => r.map(cellToString));
  }
  throw new Error("Formato não suportado. Use .csv ou .xlsx.");
}

