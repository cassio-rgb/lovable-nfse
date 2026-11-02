import { beforeEach, describe, expect, it } from "vitest";
import {
  catalogo,
  classesNFSe,
  csts,
  indopsNFSe,
  pesquisar,
  validarCatalogo,
} from "@/lib/catalogos";
import { canonical, dadosVazios, hashDados, revisaoValida } from "@/lib/domain";
import { createDemoSource } from "@/lib/datasource";
import type { Rascunho, SelecaoFiscal } from "@/lib/contracts";

export const selecao = (): SelecaoFiscal => ({
  catalogoId: catalogo.id,
  servico: "010101",
  nbs: "1.0101.11.00",
  cst: "000",
  cClassTrib: "000001",
  cIndOp: "010101",
});
const dados = () => ({
  ...dadosVazios(),
  tomador: { documento: "52998224725", nome: "Maria Fictícia" },
  operacao: "locacao" as const,
  competencia: "2026-11",
  valor: "350.00",
  descricao: "Taxa de administração",
  fiscal: selecao(),
});

describe("catálogo e integridade da seleção", () => {
  it("contagens integrais e filtro NFS-e", () => {
    expect(catalogo.servicos).toHaveLength(338);
    expect(catalogo.nbs).toHaveLength(918);
    expect(catalogo.classes).toHaveLength(173);
    expect(classesNFSe).toHaveLength(73);
    expect(csts).toHaveLength(12);
    expect(indopsNFSe).toHaveLength(28);
  });
  it("pesquisa código normalizado e descrição sem acento", () => {
    expect(pesquisar(catalogo.nbs, "101011100").some((v) => v.codigo === "1.0101.11.00")).toBe(
      true,
    );
    expect(pesquisar(catalogo.servicos, "ADMINISTRACAO").length).toBeGreaterThan(0);
    expect(pesquisar(catalogo.servicos, "zzzz inexistente")).toEqual([]);
  });
  it("valida pares e recusa documento incompatível", () => {
    expect(validarCatalogo(selecao())).toEqual({});
    expect(validarCatalogo({ ...selecao(), nbs: "9.9999.99.99" }).nbs).toBeTruthy();
    expect(validarCatalogo({ ...selecao(), cst: "200" }).cClassTrib).toBeTruthy();
    expect(validarCatalogo({ ...selecao(), cClassTrib: "000002" }).cClassTrib).toBeTruthy();
    expect(validarCatalogo({ ...selecao(), cIndOp: "010104" }).cIndOp).toBeTruthy();
    expect(validarCatalogo({ ...selecao(), catalogoId: "antigo" }).catalogo).toBeTruthy();
  });
  it("cada campo participa do hash e revisão antiga é inválida", () => {
    const d = dados();
    for (const k of Object.keys(d.fiscal) as (keyof SelecaoFiscal)[])
      expect(hashDados({ ...d, fiscal: { ...d.fiscal, [k]: "outro" } }, "A")).not.toBe(
        hashDados(d, "A"),
      );
    const { fiscal: _fiscal, ...old } = d;
    expect(JSON.parse(canonical(old))).toHaveLength(7);
    const r: Rascunho = {
      id: "r",
      empresaId: "A",
      versao: 1,
      dados: old,
      origem: { tipo: "manual" },
      criadoEm: "",
      atualizadoEm: "",
      revisao: { id: "v", rascunhoId: "r", versao: 1, hash: hashDados(old, "A"), em: "" },
    };
    expect(revisaoValida(r)).toBe(false);
    expect(revisaoValida({ ...r, revisao: { ...r.revisao!, valida: true } })).toBe(false);
  });
});

describe("rascunho demonstração com tabelas", () => {
  beforeEach(() => localStorage.clear());
  it("salva incompleto, exige códigos para revisar e mantém seleção após recarregar", async () => {
    const ds = createDemoSource();
    const r = await ds.salvarRascunho("demo-bariri", {
      dados: { ...dados(), fiscal: undefined },
      origem: { tipo: "manual" },
    });
    await expect(ds.prepararRevisao("demo-bariri", r.id, r.versao)).rejects.toThrow(/pendências/);
    const saved = await ds.salvarRascunho("demo-bariri", {
      id: r.id,
      versaoEsperada: r.versao,
      dados: dados(),
      origem: r.origem,
    });
    expect((await createDemoSource().obterRascunho("demo-bariri", saved.id)).dados.fiscal).toEqual(
      selecao(),
    );
    const reviewed = await ds.prepararRevisao("demo-bariri", saved.id, saved.versao);
    expect(revisaoValida(reviewed)).toBe(true);
    const changed = await ds.salvarRascunho("demo-bariri", {
      id: saved.id,
      versaoEsperada: reviewed.versao,
      dados: { ...dados(), fiscal: { ...selecao(), nbs: "1.0101.12.00" } },
      origem: r.origem,
    });
    expect(revisaoValida(changed)).toBe(false);
  });
});
