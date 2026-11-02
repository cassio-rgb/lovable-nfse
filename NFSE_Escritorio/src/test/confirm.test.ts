import { describe, expect, it } from "vitest";
import { chaveEstavel, confirmar, type ParamsConfirmacao } from "@/lib/confirm";
import { Bloqueio, ResultadoIncerto, type DataSource } from "@/lib/datasource";
import type { Emissao } from "@/lib/contracts";

const P: ParamsConfirmacao = { empresaId: "A", rascunhoId: "r1", revisaoId: "v1", versao: 1, ambiente: "producao_restrita", chave: chaveEstavel("A", "r1", 1, "producao_restrita", "h") };

function fake(opts: { perdeResposta?: boolean; consultaFalha?: number; bloqueia?: boolean }) {
  const server: Emissao[] = [];
  const keys: string[] = [];
  let falhas = opts.consultaFalha ?? 0;
  const ds = {
    async confirmarEmissao(_e: string, rid: string, p: { chaveIdempotente: string; versao: number }) {
      keys.push(p.chaveIdempotente);
      if (opts.bloqueia) throw new Bloqueio("Operação não liberada");
      let e = server.find((x) => x.rascunhoId === rid && x.versao === p.versao);
      if (!e) { e = { id: "op1", rascunhoId: rid, versao: p.versao, ambiente: "producao_restrita" } as Emissao; server.push(e); }
      if (opts.perdeResposta) { opts.perdeResposta = false; throw new ResultadoIncerto(); }
      return e;
    },
    async buscarEmissoes(_e: string, rid: string, v: number) {
      if (falhas-- > 0) throw new TypeError("network");
      return server.filter((x) => x.rascunhoId === rid && x.versao === v);
    },
  } as unknown as DataSource;
  return { ds, server, keys };
}

describe("confirmação com resposta perdida (M01)", () => {
  it("recupera a operação já registrada sem segundo envio", async () => {
    const f = fake({ perdeResposta: true });
    const r = await confirmar(f.ds, P, { jaTentou: false });
    expect(r).toEqual({ tipo: "ok", emissao: f.server[0] });
    expect(f.keys).toHaveLength(1);
  });
  it("fica incerto se a consulta também falha; depois só consulta", async () => {
    const f = fake({ perdeResposta: true, consultaFalha: 1 });
    expect((await confirmar(f.ds, P, { jaTentou: false })).tipo).toBe("incerto");
    const r2 = await confirmar(f.ds, P, { jaTentou: true });
    expect(r2.tipo).toBe("ok");
    expect(f.keys).toHaveLength(1);
    expect(f.server).toHaveLength(1);
  });
  it("sem operação registrada, repete apenas com a mesma chave estável", async () => {
    const f = fake({});
    await confirmar(f.ds, P, { jaTentou: true });
    expect(f.keys).toEqual([P.chave]);
  });
  it("recusa do serviço não é tratada como incerta", async () => {
    const f = fake({ bloqueia: true });
    expect(await confirmar(f.ds, P, { jaTentou: false })).toEqual({ tipo: "bloqueio", mensagem: "Operação não liberada" });
  });
  it("chave muda quando muda conteúdo ou ambiente", () => {
    expect(chaveEstavel("A", "r1", 1, "producao", "h")).not.toBe(P.chave);
    expect(chaveEstavel("A", "r1", 1, "producao_restrita", "h2")).not.toBe(P.chave);
  });
});
