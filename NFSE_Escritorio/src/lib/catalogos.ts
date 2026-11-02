import raw from "../../shared/catalogos-fiscais.json";
import type { SelecaoFiscal } from "./contracts";

export interface OpcaoFiscal {
  codigo: string;
  descricao: string;
}
export const catalogo = raw;
// A fonte inclui um marcador 9.9999.99.99 sem descrição; preservar no arquivo, não oferecer para escolha.
export const nbsDisponiveis = catalogo.nbs.filter((c) => !!c.descricao);
export const classesNFSe = catalogo.classes.filter((c) => c.nfse);
export const indopsNFSe = catalogo.indops.filter((c) => c.nfse);
export const csts: OpcaoFiscal[] = Array.from(
  new Map(classesNFSe.map((c) => [c.cst, { codigo: c.cst, descricao: c.descricaoCst }])).values(),
);
export const fiscalVazio = (): SelecaoFiscal => ({
  catalogoId: catalogo.id,
  servico: "",
  nbs: "",
  cst: "",
  cClassTrib: "",
  cIndOp: "",
});
export const fiscalCanonical = (s: SelecaoFiscal) => [
  s.catalogoId,
  s.servico,
  s.nbs,
  s.cst,
  s.cClassTrib,
  s.cIndOp,
];
const norm = (s: string) =>
  s
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
export function pesquisar<T extends OpcaoFiscal>(opcoes: T[], termo: string): T[] {
  const q = norm(termo.trim());
  const digits = q.replace(/\D/g, "");
  return opcoes.filter(
    (o) =>
      norm(o.codigo + " " + o.descricao).includes(q) ||
      (!!digits && /^[\d.\s]+$/.test(q) && o.codigo.replace(/\D/g, "").includes(digits)),
  );
}
export function validarCatalogo(
  s?: SelecaoFiscal | null,
): Partial<Record<keyof SelecaoFiscal | "catalogo", string>> {
  if (!s) return { catalogo: "Selecione os códigos fiscais antes de revisar." };
  const p: Partial<Record<keyof SelecaoFiscal | "catalogo", string>> = {};
  if (s.catalogoId !== catalogo.id)
    p.catalogo = "Seleção vinculada a outra versão das tabelas. Confira e selecione novamente.";
  const fields: [keyof SelecaoFiscal, OpcaoFiscal[], string][] = [
    ["servico", catalogo.servicos, "serviço nacional"],
    ["nbs", nbsDisponiveis, "NBS"],
    ["cst", csts, "CST IBS/CBS"],
    ["cClassTrib", classesNFSe, "cClassTrib para NFS-e"],
    ["cIndOp", indopsNFSe, "indicador de operação para NFS-e"],
  ];
  for (const [k, options, label] of fields)
    if (!options.some((o) => o.codigo === s[k])) p[k] = `Selecione um código válido de ${label}.`;
  const c = classesNFSe.find((v) => v.codigo === s.cClassTrib);
  if (c && c.cst !== s.cst) p.cClassTrib = "O cClassTrib não corresponde ao CST selecionado.";
  return p;
}
export function fiscalLinhas(s?: SelecaoFiscal) {
  const fields: [string, string | undefined, OpcaoFiscal[]][] = [
    ["Serviço nacional", s?.servico, catalogo.servicos],
    ["NBS", s?.nbs, catalogo.nbs],
    ["CST IBS/CBS", s?.cst, csts],
    ["cClassTrib", s?.cClassTrib, classesNFSe],
    ["Indicador da operação", s?.cIndOp, indopsNFSe],
  ];
  return fields.map(([label, code, options]) => ({
    label,
    texto: code
      ? `${code} — ${options.find((o) => o.codigo === code)?.descricao ?? "Código não encontrado nesta versão"}`
      : "Não selecionado",
  }));
}
