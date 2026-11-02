import { catalogo } from "@/lib/catalogos";
import { describe, expect, it } from "vitest";
import { dadosVazios, hashDados, parseMoney, podeTransmitir, revisaoValida, validCNPJ, validarDados } from "@/lib/domain";
import { analisar, chaveOrigem, parseCSV } from "@/lib/imports";
import { canonical } from "@/lib/domain";
import type { Emissao, Rascunho } from "@/lib/contracts";

const dados = () => ({
  ...dadosVazios(),
  tomador: { documento: "529.982.247-25", nome: "Maria Fictícia" },
  operacao: "locacao" as const,
  competencia: "2026-11",
  valor: "350.00",
  descricao: "Taxa de administração",
});

describe("dinheiro", () => {
  it("converte formato BR sem float", () => expect(parseMoney("1.234,56")).toEqual({ ok: true, value: "1234.56" }));
  it("rejeita mais de duas casas", () => expect(parseMoney("10,555").ok).toBe(false));
});

describe("documentos", () => {
  it("valida CNPJ fictício", () => expect(validCNPJ("11.222.333/0001-81")).toBe(true));
  it("rascunho completo não tem pendências", () => expect(validarDados(dados())).toEqual({}));
  it("CNPJ alfanumérico é recusado explicitamente, sem remover letras", () => {
    // "A1.222.333/0001-81" viraria um CNPJ numérico válido se as letras fossem descartadas.
    const d = { ...dados(), tomador: { documento: "A11.222.333/0001-81", nome: "X" } };
    expect(validarDados(d).documento).toMatch(/alfanumérico/);
  });
});

describe("revisão (versão crítica)", () => {
  const base: Rascunho = { id: "r1", empresaId: "e1", versao: 2, dados: { ...dados(), fiscal: { catalogoId: catalogo.id, servico: "010101", nbs: "1.0101.11.00", cst: "000", cClassTrib: "000001", cIndOp: "010101" } }, origem: { tipo: "manual" }, criadoEm: "", atualizadoEm: "" };
  const revisado = { ...base, revisao: { id: "v", rascunhoId: "r1", versao: 2, hash: hashDados(base.dados, "e1"), em: "" } };
  it("revisão vale para a mesma versão", () => expect(revisaoValida(revisado)).toBe(true));
  it("alterar valor invalida a revisão", () => expect(revisaoValida({ ...revisado, versao: 3, dados: { ...base.dados, valor: "351.00" } })).toBe(false));
});

describe("resultado desconhecido (M01)", () => {
  it("não permite reenvio", () => {
    const r: Rascunho = { id: "r1", empresaId: "e1", versao: 1, dados: { ...dados(), fiscal: { catalogoId: catalogo.id, servico: "010101", nbs: "1.0101.11.00", cst: "000", cClassTrib: "000001", cIndOp: "010101" } }, origem: { tipo: "manual" }, criadoEm: "", atualizadoEm: "" };
    const rv = { ...r, revisao: { id: "v", rascunhoId: "r1", versao: 1, hash: hashDados(r.dados, "e1"), em: "" } };
    const e = { estado: "resultado_desconhecido" } as Emissao;
    expect(podeTransmitir(rv, e).ok).toBe(false);
  });
});

describe("importação (M02)", () => {
  const csv =
    "id_origem;tomador_documento;tomador_nome;operacao;competencia;valor;descricao\n" +
    "A1;529.982.247-25;Maria;locacao;11/2026;100,00;Administração nov\n" +
    "A2;529.982.247-25;João;locacao;11/2026;200,00;Administração nov\n" +
    "A3;000;Inválido;locacao;11/2026;50,00;Administração nov\n" +
    "A4;529.982.247-25;Ana;locacao;11/2026;300,00;Administração nov\n";
  it("classifica válida, inválida e duplicada com totais", () => {
    const rows = parseCSV(csv);
    const first = analisar(rows, new Map());
    const a4 = first.linhas.find((l) => l.idOrigem === "A4")!;
    const imp = new Map([[chaveOrigem("planilha", "A4"), canonical(a4.dados)]]);
    const p = analisar(rows, imp);
    expect(p.totais.valida).toEqual({ qtd: 2, valor: "300.00" });
    expect(p.totais.invalida.qtd).toBe(1);
    expect(p.totais.duplicada).toEqual({ qtd: 1, valor: "300.00" });
  });
});
