import type { Ambiente, Cenario, Emissao } from "./contracts";
import { AcessoNegado, Bloqueio, ConflitoVersao, ResultadoIncerto, type DataSource } from "./datasource";

/** Chave estável: mesma empresa/rascunho/versão/ambiente/conteúdo revisado => mesma chave, mesmo após recarga. */
export function chaveEstavel(empresaId: string, rascunhoId: string, versao: number, ambiente: Ambiente, hash: string): string {
  return `emissao:${empresaId}:${rascunhoId}:v${versao}:${ambiente}:${hash}`;
}

export type ResultadoConfirmacao =
  | { tipo: "ok"; emissao: Emissao }
  | { tipo: "incerto" }
  | { tipo: "conflito" }
  | { tipo: "bloqueio"; mensagem: string };

export interface ParamsConfirmacao {
  empresaId: string;
  rascunhoId: string;
  revisaoId: string;
  versao: number;
  ambiente: Ambiente;
  chave: string;
  cenario?: Cenario | undefined;
}

/** Consulta se o comando já existe. Nunca envia nada. */
export async function recuperar(ds: DataSource, p: ParamsConfirmacao): Promise<Emissao | null> {
  const found = await ds.buscarEmissoes(p.empresaId, p.rascunhoId, p.versao);
  return found.find((e) => e.ambiente === p.ambiente) ?? null;
}

/**
 * Confirma a emissão. Antes de qualquer nova tentativa, consulta se a operação já existe.
 * Falha de comunicação vira "incerto" (não "não enviado"): a UI só oferece consulta.
 */
export async function confirmar(ds: DataSource, p: ParamsConfirmacao, opts: { jaTentou: boolean }): Promise<ResultadoConfirmacao> {
  if (opts.jaTentou) {
    try {
      const existente = await recuperar(ds, p);
      if (existente) return { tipo: "ok", emissao: existente };
    } catch {
      return { tipo: "incerto" };
    }
  }
  try {
    const e = await ds.confirmarEmissao(p.empresaId, p.rascunhoId, {
      revisaoId: p.revisaoId,
      versao: p.versao,
      ambiente: p.ambiente,
      chaveIdempotente: p.chave,
      cenario: p.cenario,
    });
    return { tipo: "ok", emissao: e };
  } catch (e) {
    if (e instanceof ConflitoVersao) return { tipo: "conflito" };
    if (e instanceof Bloqueio || e instanceof AcessoNegado) return { tipo: "bloqueio", mensagem: e.message };
    // Qualquer outra falha (rede, timeout, 5xx, resposta ilegível): o comando pode ter sido registrado.
    if (e instanceof ResultadoIncerto || e instanceof Error) {
      try {
        const existente = await recuperar(ds, p);
        if (existente) return { tipo: "ok", emissao: existente };
      } catch {
        /* consulta também falhou: continua incerto */
      }
    }
    return { tipo: "incerto" };
  }
}
