import { describe, expect, it } from "vitest";
import { previaDaApi } from "@/lib/datasource";

describe("prévia da importação vinda do serviço fiscal", () => {
  it("usa a classificação e os totais do servidor", () => {
    const p = previaDaApi({
      layout: "nfse-imoveis-v1",
      totais: { valida: { qtd: 1, valor: "100.00" }, invalida: { qtd: 1, valor: "0" } },
      linhas: [
        { linha: 2, sistema: "planilha", idOrigem: "A1", situacao: "valida", erros: [], dados: { tomador: { documento: "1", nome: "M" }, operacao: "locacao", competencia: "2026-11", valor: "100.00", descricao: "x", imovel: "" } },
        { linha: 3, sistema: "planilha", idOrigem: "A2", situacao: "invalida", erros: ["CPF ou CNPJ inválido."], dados: { tomador: { documento: "0", nome: "J" }, operacao: "locacao", competencia: "2026-11", valor: "", descricao: "x", imovel: "" } },
      ],
    });
    expect(p.totais.valida).toEqual({ qtd: 1, valor: "100.00" });
    expect(p.totais.duplicada).toEqual({ qtd: 0, valor: "0.00" });
    expect(p.linhas.map((l) => [l.situacao, l.valorCentavos])).toEqual([["valida", 10000n], ["invalida", 0n]]);
  });
});
