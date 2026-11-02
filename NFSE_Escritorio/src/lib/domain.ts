import type {
  Ambiente,
  DadosRascunho,
  Emissao,
  EstadoFiscal,
  Liberacao,
  Rascunho,
  TipoOperacao,
} from "./contracts";

/* ---------- Dinheiro (centavos inteiros, sem float) ---------- */

/** Converte entrada BR ("1.234,56") ou canônica ("1234.56") para decimal canônico. Rejeita >2 casas. */
export function parseMoney(raw: string): { ok: true; value: string } | { ok: false; erro: string } {
  const s = raw.trim().replace(/^R\$\s*/, "");
  if (!s) return { ok: false, erro: "Informe o valor." };
  let norm: string;
  if (s.includes(",")) norm = s.replace(/\./g, "").replace(",", ".");
  else if (/^\d{1,3}(\.\d{3})+$/.test(s)) norm = s.replace(/\./g, "");
  else norm = s;
  const m = /^(\d+)(?:\.(\d+))?$/.exec(norm);
  if (!m) return { ok: false, erro: "Valor monetário inválido." };
  const frac = m[2] ?? "";
  if (frac.length > 2) return { ok: false, erro: "Informe no máximo duas casas decimais." };
  const int = m[1]!.replace(/^0+(?=\d)/, "");
  const value = `${int}.${frac.padEnd(2, "0")}`;
  if (value === "0.00") return { ok: false, erro: "O valor deve ser maior que zero." };
  return { ok: true, value };
}

export function toCents(canon: string): bigint {
  const [i, f = "00"] = canon.split(".");
  return BigInt(i ?? "0") * 100n + BigInt(f.padEnd(2, "0").slice(0, 2));
}

export function fromCents(c: bigint): string {
  const neg = c < 0n;
  const a = neg ? -c : c;
  return `${neg ? "-" : ""}${a / 100n}.${(a % 100n).toString().padStart(2, "0")}`;
}

export function formatBRL(canon: string): string {
  if (!canon) return "—";
  const [i, f] = canon.split(".");
  return `R$ ${(i ?? "0").replace(/\B(?=(\d{3})+(?!\d))/g, ".")},${f}`;
}

/* ---------- Documentos ---------- */

export const onlyDigits = (s: string) => s.replace(/\D/g, "");


export function validCPF(raw: string): boolean {
  const d = onlyDigits(raw);
  if (d.length !== 11 || /^(\d)\1+$/.test(d)) return false;
  const dv = (n: number) => {
    let s = 0;
    for (let i = 0; i < n; i++) s += Number(d[i]) * (n + 1 - i);
    const r = (s * 10) % 11;
    return r === 10 ? 0 : r;
  };
  return dv(9) === Number(d[9]) && dv(10) === Number(d[10]);
}

export function validCNPJ(raw: string): boolean {
  const d = onlyDigits(raw);
  if (d.length !== 14 || /^(\d)\1+$/.test(d)) return false;
  const dv = (n: number) => {
    const w = n === 12 ? [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] : [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    const s = w.reduce((acc, wi, i) => acc + Number(d[i]) * wi, 0);
    const r = s % 11;
    return r < 2 ? 0 : 11 - r;
  };
  return dv(12) === Number(d[12]) && dv(13) === Number(d[13]);
}

export function formatDoc(raw: string): string {
  const d = onlyDigits(raw);
  if (d.length === 14) return d.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
  if (d.length === 11) return d.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4");
  return raw;
}

/* ---------- Validação do rascunho ---------- */

import { validarCatalogo, fiscalCanonical } from "./catalogos";

export type Pendencias = Partial<Record<"documento" | "nome" | "operacao" | "competencia" | "valor" | "descricao" | "catalogo", string>>;

export function validarDados(d: DadosRascunho, revisar = false): Pendencias {
  const p: Pendencias = {};
  const doc = onlyDigits(d.tomador.documento);
  if (/[A-Za-z]/.test(d.tomador.documento)) p.documento = "CPF/CNPJ com letras (CNPJ alfanumérico) ainda não é suportado.";
  else if (!doc) p.documento = "Informe o CPF ou CNPJ do tomador.";
  else if (!(doc.length === 11 ? validCPF(doc) : doc.length === 14 ? validCNPJ(doc) : false))
    p.documento = "CPF ou CNPJ inválido.";
  if (!d.tomador.nome.trim()) p.nome = "Informe o nome do tomador.";
  if (!d.operacao) p.operacao = "Selecione o tipo de operação.";
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(d.competencia)) p.competencia = "Informe a competência (mês/ano).";
  const v = parseMoney(d.valor);
  if (!v.ok) p.valor = v.erro;
  if (d.descricao.trim().length < 5) p.descricao = "Descreva o serviço (mínimo 5 caracteres).";
  if (revisar) {
    const erros = Object.values(validarCatalogo(d.fiscal));
    if (erros.length) p.catalogo = erros.join(" ");
  }
  return p;
}

/* ---------- Hash de versão crítica ---------- */

export function canonical(d: DadosRascunho): string {
  return JSON.stringify([
    onlyDigits(d.tomador.documento),
    d.tomador.nome.trim(),
    d.operacao,
    d.competencia,
    d.valor,
    d.descricao.trim(),
    d.imovel.trim(),
    ...(d.fiscal ? [fiscalCanonical(d.fiscal)] : []),
  ]);
}

/** FNV-1a 64 bits — identifica conteúdo para revisão; não é prova criptográfica. */
export function hashDados(d: DadosRascunho, empresaId: string): string {
  const s = empresaId + "|" + canonical(d);
  let h = 0xcbf29ce484222325n;
  for (let i = 0; i < s.length; i++) {
    h ^= BigInt(s.charCodeAt(i));
    h = (h * 0x100000001b3n) & 0xffffffffffffffffn;
  }
  return h.toString(16).padStart(16, "0");
}

export function revisaoValida(r: Rascunho): boolean {
  if (Object.keys(validarCatalogo(r.dados.fiscal)).length) return false;
  if (r.revisao?.valida !== undefined) return r.revisao.valida && r.revisao.versao === r.versao;
  return !!r.revisao && r.revisao.versao === r.versao && r.revisao.hash === hashDados(r.dados, r.empresaId);
}

/* ---------- Elegibilidade (M04) ---------- */

export function liberado(
  libs: Liberacao[],
  empresaId: string,
  operacao: TipoOperacao | "",
  ambiente: Ambiente,
): Liberacao | undefined {
  if (!operacao) return undefined;
  return libs.find((l) => l.empresaId === empresaId && l.operacao === operacao && l.ambiente === ambiente);
}

/* ---------- Estados (M01) ---------- */

const TERMINAIS_SEM_REENVIO: EstadoFiscal[] = ["na_fila", "transmitindo", "resultado_desconhecido", "emitida"];

/** Pode criar nova transmissão a partir deste rascunho? Nunca com resultado desconhecido. */
export function podeTransmitir(r: Rascunho, emissao: Emissao | undefined): { ok: boolean; motivo?: string } {
  if (emissao && TERMINAIS_SEM_REENVIO.includes(emissao.estado)) {
    return {
      ok: false,
      motivo:
        emissao.estado === "resultado_desconhecido"
          ? "O resultado do envio anterior é desconhecido. Verifique a situação; reenviar poderia duplicar a nota."
          : "Esta operação já foi enviada.",
    };
  }
  if (!revisaoValida(r)) return { ok: false, motivo: "A revisão não corresponde à versão atual. Revise novamente." };
  return { ok: true };
}

export function estadoRascunho(r: Rascunho): EstadoFiscal {
  if (Object.keys(validarDados(r.dados, true)).length) return "com_pendencias";
  return revisaoValida(r) ? "revisado" : "rascunho";
}

export function dadosVazios(): DadosRascunho {
  return {
    tomador: { documento: "", nome: "", email: "" },
    operacao: "",
    competencia: "",
    valor: "",
    descricao: "",
    imovel: "",
  };
}
