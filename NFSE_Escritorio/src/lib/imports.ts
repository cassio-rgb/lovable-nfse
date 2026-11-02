import type { DadosRascunho, TipoOperacao } from "./contracts";
import { canonical, fromCents, parseMoney, toCents, validarDados } from "./domain";

export const LAYOUT_VERSAO = "nfse-imoveis-v1";
export const COLUNAS = [
  "id_origem",
  "sistema_origem",
  "tomador_documento",
  "tomador_nome",
  "tomador_email",
  "operacao",
  "competencia",
  "valor",
  "descricao",
  "imovel",
] as const;
export const OBRIGATORIAS = ["id_origem", "tomador_documento", "tomador_nome", "operacao", "competencia", "valor", "descricao"];
export const MAX_LINHAS = 5000;
export const MAX_BYTES = 5 * 1024 * 1024;

export type SituacaoLinha = "valida" | "invalida" | "duplicada" | "conflito" | "repetida_no_arquivo";

export interface LinhaPrevia {
  linha: number;
  idOrigem: string;
  sistema: string;
  dados: DadosRascunho;
  situacao: SituacaoLinha;
  erros: string[];
  valorCentavos: bigint;
}

export interface Previa {
  layout: string;
  linhas: LinhaPrevia[];
  totais: Record<SituacaoLinha, { qtd: number; valor: string }>;
  erroArquivo?: string | undefined;
}

/** Registro já importado: chave = sistema|id_origem, conteúdo = canonical(dados). */
export type Importados = Map<string, string>;

export const chaveOrigem = (sistema: string, id: string) => `${sistema || "planilha"}|${id}`;

const OPS: Record<string, TipoOperacao> = {
  locacao: "locacao",
  "locação": "locacao",
  aluguel: "locacao",
  venda: "venda",
  arrendamento: "arrendamento",
  administracao: "administracao",
  "administração": "administracao",
};

function normCompetencia(s: string): string {
  const t = s.trim();
  let m = /^(\d{4})-(\d{1,2})$/.exec(t);
  if (m) return `${m[1]}-${m[2]!.padStart(2, "0")}`;
  m = /^(\d{1,2})\/(\d{4})$/.exec(t);
  if (m) return `${m[2]}-${m[1]!.padStart(2, "0")}`;
  return t;
}

/** Parser CSV com aspas (RFC 4180), separador ; ou , detectado no cabeçalho. Nunca avalia fórmulas. */
export function parseCSV(text: string): string[][] {
  const clean = text.replace(/^\uFEFF/, "");
  const first = clean.split(/\r?\n/, 1)[0] ?? "";
  const sep = (first.match(/;/g)?.length ?? 0) >= (first.match(/,/g)?.length ?? 0) ? ";" : ",";
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let q = false;
  for (let i = 0; i < clean.length; i++) {
    const c = clean[i];
    if (q) {
      if (c === '"' && clean[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') q = false;
      else cell += c;
    } else if (c === '"') q = true;
    else if (c === sep) { row.push(cell); cell = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && clean[i + 1] === "\n") i++;
      row.push(cell); rows.push(row); row = []; cell = "";
    } else cell += c;
  }
  if (cell !== "" || row.length) { row.push(cell); rows.push(row); }
  return rows.filter((r) => r.some((c) => c.trim() !== ""));
}

const vazio = (): Previa["totais"] => ({
  valida: { qtd: 0, valor: "0.00" },
  invalida: { qtd: 0, valor: "0.00" },
  duplicada: { qtd: 0, valor: "0.00" },
  conflito: { qtd: 0, valor: "0.00" },
  repetida_no_arquivo: { qtd: 0, valor: "0.00" },
});

export function analisar(rows: string[][], importados: Importados): Previa {
  if (rows.length < 2) return { layout: LAYOUT_VERSAO, linhas: [], totais: vazio(), erroArquivo: "Arquivo sem linhas de dados." };
  if (rows.length - 1 > MAX_LINHAS)
    return { layout: LAYOUT_VERSAO, linhas: [], totais: vazio(), erroArquivo: `Limite de ${MAX_LINHAS} linhas excedido.` };
  const head = rows[0]!.map((h) => h.trim().toLowerCase());
  const faltando = OBRIGATORIAS.filter((c) => !head.includes(c));
  if (faltando.length)
    return { layout: LAYOUT_VERSAO, linhas: [], totais: vazio(), erroArquivo: `Colunas obrigatórias ausentes: ${faltando.join(", ")}.` };
  const col = (r: string[], n: string) => (r[head.indexOf(n)] ?? "").toString().trim();
  const vistos = new Set<string>();
  const somas: Record<SituacaoLinha, bigint> = { valida: 0n, invalida: 0n, duplicada: 0n, conflito: 0n, repetida_no_arquivo: 0n };
  const totais = vazio();
  const linhas: LinhaPrevia[] = rows.slice(1).map((r, i) => {
    const erros: string[] = [];
    const idOrigem = col(r, "id_origem");
    const sistema = col(r, "sistema_origem") || "planilha";
    const opRaw = col(r, "operacao").toLowerCase();
    const op = OPS[opRaw];
    if (opRaw && !op) erros.push(`Operação "${col(r, "operacao")}" não reconhecida.`);
    const mv = parseMoney(col(r, "valor"));
    const dados: DadosRascunho = {
      tomador: { documento: col(r, "tomador_documento"), nome: col(r, "tomador_nome"), email: col(r, "tomador_email") },
      operacao: op ?? "",
      competencia: normCompetencia(col(r, "competencia")),
      valor: mv.ok ? mv.value : "",
      descricao: col(r, "descricao"),
      imovel: col(r, "imovel"),
    };
    if (!idOrigem) erros.push("id_origem vazio: sem identificador estável a linha não pode ser importada.");
    for (const [k, msg] of Object.entries(validarDados(dados))) {
      if (k === "valor" && !mv.ok) erros.push(`Valor: ${mv.erro}`);
      else if (!(k === "operacao" && opRaw && !op)) erros.push(msg as string);
    }
    const valorCentavos = mv.ok ? toCents(mv.value) : 0n;
    let situacao: SituacaoLinha;
    const chave = chaveOrigem(sistema, idOrigem);
    if (erros.length) situacao = "invalida";
    else if (vistos.has(chave)) situacao = "repetida_no_arquivo";
    else if (importados.has(chave)) situacao = importados.get(chave) === canonical(dados) ? "duplicada" : "conflito";
    else situacao = "valida";
    if (idOrigem) vistos.add(chave);
    somas[situacao] += valorCentavos;
    totais[situacao].qtd++;
    return { linha: i + 2, idOrigem, sistema, dados, situacao, erros, valorCentavos };
  });
  for (const k of Object.keys(somas) as SituacaoLinha[]) totais[k].valor = fromCents(somas[k]);
  return { layout: LAYOUT_VERSAO, linhas, totais };
}

export const MODELO_CSV =
  "id_origem;sistema_origem;tomador_documento;tomador_nome;tomador_email;operacao;competencia;valor;descricao;imovel\n" +
  "LOC-2026-11-001;planilha;529.982.247-25;Maria Fictícia da Silva;maria@exemplo.test;locacao;11/2026;350,00;Taxa de administração de locação - novembro;Rua Exemplo, 100 - Apto 12\n";
