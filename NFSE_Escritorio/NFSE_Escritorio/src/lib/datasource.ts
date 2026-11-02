import type {
  Ambiente,
  Cenario,
  DadosRascunho,
  Emissao,
  Empresa,
  Liberacao,
  Origem,
  Papel,
  Rascunho,
} from "./contracts";
import { canonical, hashDados, liberado, podeTransmitir, validarDados } from "./domain";
import { analisar, chaveOrigem, type Importados, type LinhaPrevia, type Previa, type SituacaoLinha } from "./imports";
import { lerArquivo } from "./import-file";
import { toCents } from "./domain";

export class AcessoNegado extends Error {
  constructor() {
    super("Acesso não disponível.");
  }
}
export class ConflitoVersao extends Error {
  constructor() {
    super("Este rascunho foi alterado em outra janela. Recarregue para ver a versão atual.");
  }
}
export class Bloqueio extends Error {}
export class NaoAutenticado extends Error {}
/** A requisição pode ter chegado ao servidor, mas a resposta não foi recebida/interpretada. */
export class ResultadoIncerto extends Error {
  constructor() {
    super("A resposta da confirmação não foi recebida.");
  }
}

export interface Sessao {
  usuario: string;
  papel: Papel;
  empresas: Empresa[];
  liberacoes: Liberacao[];
}

export interface SalvarInput {
  id?: string | undefined;
  versaoEsperada?: number | undefined;
  dados: DadosRascunho;
  origem: Origem;
}

export interface DataSource {
  modo: "demo" | "api";
  sessao(): Promise<Sessao>;
  listarRascunhos(empresaId: string): Promise<Rascunho[]>;
  obterRascunho(empresaId: string, id: string): Promise<Rascunho>;
  salvarRascunho(empresaId: string, input: SalvarInput): Promise<Rascunho>;
  descartarRascunho(empresaId: string, id: string): Promise<void>;
  importados(empresaId: string): Promise<Importados>;
  analisarImportacao(empresaId: string, arquivo: File): Promise<Previa>;
  confirmarImportacao(empresaId: string, linhas: LinhaPrevia[]): Promise<{ criados: number; ignorados: number }>;
  prepararRevisao(empresaId: string, id: string, versao: number): Promise<Rascunho>;
  confirmarEmissao(
    empresaId: string,
    id: string,
    p: { revisaoId: string; versao: number; ambiente: Ambiente; chaveIdempotente: string; cenario?: Cenario | undefined },
  ): Promise<Emissao>;
  listarEmissoes(empresaId: string): Promise<Emissao[]>;
  buscarEmissoes(empresaId: string, rascunhoId: string, versao: number): Promise<Emissao[]>;
  obterEmissao(empresaId: string, id: string): Promise<Emissao>;
  verificarSituacao(empresaId: string, id: string): Promise<Emissao>;
}

/* ================= Modo demonstração (somente dados fictícios, localStorage) ================= */

const KEY = "nfse-imoveis:demo:v1";
interface DemoDB {
  rascunhos: Rascunho[];
  emissoes: Emissao[];
  importados: Record<string, Record<string, string>>; // empresaId -> chave -> canonical
  idem: Record<string, string>; // chave idempotente -> emissaoId
  seq: number;
}

export const DEMO_EMPRESAS: Empresa[] = [
  { id: "demo-bariri", razaoSocial: "Imobiliária Fictícia Bariri Ltda", cnpj: "11.222.333/0001-81", municipio: "Bariri/SP", ficticia: true },
  { id: "demo-pederneiras", razaoSocial: "Gestora Exemplo Pederneiras ME", cnpj: "45.723.174/0001-10", municipio: "Pederneiras/SP", ficticia: true },
  { id: "demo-sem-liberacao", razaoSocial: "Administradora Teste Sem Liberação", cnpj: "60.891.235/0001-42", municipio: "Bariri/SP", ficticia: true },
];

export const DEMO_LIBERACOES: Liberacao[] = [
  { empresaId: "demo-bariri", operacao: "locacao", ambiente: "producao_restrita", versao: 1, evidencia: "Liberação fictícia de demonstração" },
  { empresaId: "demo-pederneiras", operacao: "administracao", ambiente: "producao_restrita", versao: 1, evidencia: "Liberação fictícia de demonstração" },
];

const now = () => new Date().toISOString();
const uid = (p: string) => `${p}-${Math.random().toString(36).slice(2, 10)}${Date.now().toString(36).slice(-4)}`;

function load(): DemoDB {
  if (typeof window === "undefined") return { rascunhos: [], emissoes: [], importados: {}, idem: {}, seq: 0 };
  try {
    const raw = window.localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    /* ignora estado corrompido */
  }
  return { rascunhos: [], emissoes: [], importados: {}, idem: {}, seq: 0 };
}
function save(db: DemoDB) {
  window.localStorage.setItem(KEY, JSON.stringify(db));
}
const delay = (ms = 120) => new Promise((r) => setTimeout(r, ms));

function autorizado(empresaId: string) {
  if (!DEMO_EMPRESAS.some((e) => e.id === empresaId)) throw new AcessoNegado();
}

/** Progressão simulada derivada do tempo: sobrevive a recarga e não reenvia nada. */
function progredir(e: Emissao): Emissao {
  if (!e.simulacao) return e;
  const dt = Date.now() - Date.parse(e.criadoEm);
  if (e.estado === "na_fila" && dt > 1200) e = { ...e, estado: "transmitindo", atualizadoEm: now() };
  if (e.estado === "transmitindo" && dt > 3500) {
    if (e.cenario === "aceita")
      e = { ...e, estado: "emitida", atualizadoEm: now(), retorno: { numero: `SIM-${e.identidadeDps.slice(-6)}`, chave: `SIMULACAO-${e.identidadeDps}`, mensagem: "Simulação: aceita. Nenhum documento fiscal foi emitido." } };
    else if (e.cenario === "rejeitada")
      e = { ...e, estado: "rejeitada", atualizadoEm: now(), retorno: { codigo: "SIM-E0000", mensagem: "Simulação: o CPF/CNPJ do tomador não foi aceito. Confira o documento e gere uma nova revisão.", detalheTecnico: "Código simulado SIM-E0000 — não corresponde a catálogo oficial." } };
    else e = { ...e, estado: "resultado_desconhecido", atualizadoEm: now(), retorno: { mensagem: "Simulação: a resposta foi perdida após o envio. Não sabemos se a nota foi emitida." } };
  }
  return e;
}

export function createDemoSource(): DataSource {
  return {
    modo: "demo",
    async sessao() {
      return { usuario: "Operador de demonstração", papel: "escritorio", empresas: DEMO_EMPRESAS, liberacoes: DEMO_LIBERACOES };
    },
    async listarRascunhos(empresaId) {
      autorizado(empresaId);
      await delay(40);
      return load().rascunhos.filter((r) => r.empresaId === empresaId && !r.emissaoId).sort((a, b) => b.atualizadoEm.localeCompare(a.atualizadoEm));
    },
    async obterRascunho(empresaId, id) {
      autorizado(empresaId);
      const r = load().rascunhos.find((x) => x.id === id);
      if (!r || r.empresaId !== empresaId) throw new AcessoNegado();
      return r;
    },
    async salvarRascunho(empresaId, input) {
      autorizado(empresaId);
      await delay();
      const db = load();
      if (input.id) {
        const i = db.rascunhos.findIndex((x) => x.id === input.id);
        const cur = db.rascunhos[i];
        if (!cur || cur.empresaId !== empresaId) throw new AcessoNegado();
        if (cur.emissaoId) throw new Bloqueio("Este rascunho já foi enviado e não pode ser alterado.");
        if (cur.versao !== input.versaoEsperada) throw new ConflitoVersao();
        const changed = canonical(cur.dados) !== canonical(input.dados);
        const next: Rascunho = changed
          ? { ...cur, dados: input.dados, versao: cur.versao + 1, atualizadoEm: now(), revisao: undefined }
          : cur;
        db.rascunhos[i] = next;
        save(db);
        return next;
      }
      const r: Rascunho = { id: uid("rasc"), empresaId, versao: 1, dados: input.dados, origem: input.origem, criadoEm: now(), atualizadoEm: now() };
      db.rascunhos.push(r);
      save(db);
      return r;
    },
    async descartarRascunho(empresaId, id) {
      autorizado(empresaId);
      const db = load();
      const r = db.rascunhos.find((x) => x.id === id);
      if (!r || r.empresaId !== empresaId) throw new AcessoNegado();
      if (r.emissaoId) throw new Bloqueio("Rascunho já enviado não pode ser descartado.");
      db.rascunhos = db.rascunhos.filter((x) => x.id !== id);
      save(db);
    },
    async importados(empresaId) {
      autorizado(empresaId);
      return new Map(Object.entries(load().importados[empresaId] ?? {}));
    },
    async analisarImportacao(empresaId, arquivo) {
      autorizado(empresaId);
      return analisar(await lerArquivo(arquivo), new Map(Object.entries(load().importados[empresaId] ?? {})));
    },
    async confirmarImportacao(empresaId, linhas) {
      autorizado(empresaId);
      await delay(200);
      const db = load();
      const mapa = (db.importados[empresaId] ??= {});
      const loteId = uid("lote");
      let criados = 0;
      let ignorados = 0;
      // Commit atômico: monta tudo em memória e grava uma única vez.
      for (const l of linhas) {
        const k = chaveOrigem(l.sistema, l.idOrigem);
        if (l.situacao !== "valida" || mapa[k]) { ignorados++; continue; }
        mapa[k] = canonical(l.dados);
        db.rascunhos.push({
          id: uid("rasc"), empresaId, versao: 1, dados: l.dados,
          origem: { tipo: "importacao", sistema: l.sistema, idOrigem: l.idOrigem, loteId, linha: l.linha },
          criadoEm: now(), atualizadoEm: now(),
        });
        criados++;
      }
      save(db);
      return { criados, ignorados };
    },
    async prepararRevisao(empresaId, id, versao) {
      autorizado(empresaId);
      await delay();
      const db = load();
      const i = db.rascunhos.findIndex((x) => x.id === id);
      const r = db.rascunhos[i];
      if (!r || r.empresaId !== empresaId) throw new AcessoNegado();
      if (r.versao !== versao) throw new ConflitoVersao();
      if (Object.keys(validarDados(r.dados, true)).length) throw new Bloqueio("Há pendências no rascunho. Corrija antes de revisar.");
      const next = { ...r, revisao: { id: uid("rev"), rascunhoId: id, versao: r.versao, hash: hashDados(r.dados, empresaId), em: now() } };
      db.rascunhos[i] = next;
      save(db);
      return next;
    },
    async confirmarEmissao(empresaId, id, p) {
      autorizado(empresaId);
      await delay(200);
      const db = load();
      const existente = db.idem[p.chaveIdempotente];
      if (existente) return db.emissoes.find((e) => e.id === existente)!;
      const i = db.rascunhos.findIndex((x) => x.id === id);
      const r = db.rascunhos[i];
      if (!r || r.empresaId !== empresaId) throw new AcessoNegado();
      if (r.versao !== p.versao || r.revisao?.id !== p.revisaoId) throw new ConflitoVersao();
      if (p.ambiente !== "producao_restrita") throw new Bloqueio("Produção está desabilitada.");
      if (!liberado(DEMO_LIBERACOES, empresaId, r.dados.operacao, p.ambiente))
        throw new Bloqueio("Esta operação não está liberada para esta empresa e ambiente.");
      const anterior = r.emissaoId ? db.emissoes.find((e) => e.id === r.emissaoId) : undefined;
      const pode = podeTransmitir(r, anterior);
      if (!pode.ok) throw new Bloqueio(pode.motivo);
      db.seq++;
      const e: Emissao = {
        id: uid("op"), empresaId, rascunhoId: id, versao: r.versao, ambiente: p.ambiente,
        identidadeDps: `SIMDPS${String(db.seq).padStart(9, "0")}`, snapshot: r.dados, estado: "na_fila",
        simulacao: true, cenario: p.cenario ?? "aceita", criadoEm: now(), atualizadoEm: now(),
      };
      db.emissoes.push(e);
      db.rascunhos[i] = { ...r, emissaoId: e.id };
      db.idem[p.chaveIdempotente] = e.id;
      save(db);
      return e;
    },
    async listarEmissoes(empresaId) {
      autorizado(empresaId);
      const db = load();
      db.emissoes = db.emissoes.map(progredir);
      save(db);
      return db.emissoes.filter((e) => e.empresaId === empresaId).sort((a, b) => b.criadoEm.localeCompare(a.criadoEm));
    },
    async buscarEmissoes(empresaId, rascunhoId, versao) {
      autorizado(empresaId);
      return load().emissoes.filter((e) => e.empresaId === empresaId && e.rascunhoId === rascunhoId && e.versao === versao);
    },
    async obterEmissao(empresaId, id) {
      autorizado(empresaId);
      const db = load();
      const i = db.emissoes.findIndex((e) => e.id === id);
      if (i < 0 || db.emissoes[i]!.empresaId !== empresaId) throw new AcessoNegado();
      db.emissoes[i] = progredir(db.emissoes[i]!);
      save(db);
      return db.emissoes[i]!;
    },
    async verificarSituacao(empresaId, id) {
      autorizado(empresaId);
      await delay(600);
      const db = load();
      const i = db.emissoes.findIndex((e) => e.id === id);
      if (i < 0 || db.emissoes[i]!.empresaId !== empresaId) throw new AcessoNegado();
      const e = db.emissoes[i]!;
      if (e.estado !== "resultado_desconhecido") return e;
      // Consulta simulada pela identidade DPS reservada: localiza a mesma nota, sem novo envio.
      db.emissoes[i] = { ...e, estado: "emitida", atualizadoEm: now(), retorno: { numero: `SIM-${e.identidadeDps.slice(-6)}`, chave: `SIMULACAO-${e.identidadeDps}`, mensagem: "Simulação: a consulta pela identidade da DPS encontrou a nota. Nenhum documento fiscal foi emitido." } };
      save(db);
      return db.emissoes[i]!;
    },
  };
}

/* ================= Modo API (serviço fiscal Python separado) ================= */

export function createApiSource(base: string): DataSource {
  const url = (p: string) => `${base.replace(/\/$/, "")}${p}`;
  async function call<T>(path: string, init?: RequestInit, opts?: { incerto?: boolean }): Promise<T> {
    let res: Response;
    try {
      res = await fetch(url(path), {
        ...init,
        credentials: "include", // sessão em cookie HttpOnly emitida pelo serviço fiscal
        signal: AbortSignal.timeout(20000),
        // X-Requested-With é exigido pelo serviço em mutações (proteção CSRF + origem permitida).
        headers: {
          ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
          "X-Requested-With": "nfse-imoveis",
          ...(init?.headers ?? {}),
        },
      });
    } catch (e) {
      if (opts?.incerto) throw new ResultadoIncerto();
      throw e;
    }
    if (opts?.incerto && res.status >= 500) throw new ResultadoIncerto();
    if (res.status === 401) throw new NaoAutenticado();
    if (res.status === 403 || res.status === 404) throw new AcessoNegado();
    if (res.status === 409) throw new ConflitoVersao();
    const body = await res.json().catch(() => ({}));
    if (res.status === 422 || res.status === 423) throw new Bloqueio(body?.detail?.mensagem ?? "Ação bloqueada.");
    if (!res.ok) throw new Error(body?.detail?.mensagem ?? `Falha de comunicação (${res.status}).`);
    if (res.status === 204) return undefined as T;
    return body as T;
  }
  const e = (id: string) => `/v1/empresas/${encodeURIComponent(id)}`;
  return {
    modo: "api",
    sessao: () => call("/v1/sessao"),
    listarRascunhos: (emp) => call(`${e(emp)}/rascunhos`),
    obterRascunho: (emp, id) => call(`${e(emp)}/rascunhos/${id}`),
    salvarRascunho: (emp, i) =>
      i.id
        ? call(`${e(emp)}/rascunhos/${i.id}`, { method: "PUT", body: JSON.stringify({ versao_esperada: i.versaoEsperada, dados: i.dados }) })
        : call(`${e(emp)}/rascunhos`, { method: "POST", body: JSON.stringify({ dados: i.dados, origem: i.origem }) }),
    descartarRascunho: (emp, id) => call(`${e(emp)}/rascunhos/${id}`, { method: "DELETE" }),
    importados: async (emp) => new Map(Object.entries(await call<Record<string, string>>(`${e(emp)}/importacoes/origens`))),
    analisarImportacao: async (emp, arquivo) => {
      const fd = new FormData();
      fd.append("arquivo", arquivo);
      const r = await call<ApiPrevia>(`${e(emp)}/importacoes/analisar`, { method: "POST", body: fd });
      return previaDaApi(r);
    },
    confirmarImportacao: (emp, linhas) =>
      call(`${e(emp)}/importacoes/confirmar`, {
        method: "POST",
        body: JSON.stringify({ linhas: linhas.map((l) => ({ linha: l.linha, sistema: l.sistema, id_origem: l.idOrigem, dados: l.dados })) }),
      }),
    prepararRevisao: (emp, id, versao) => call(`${e(emp)}/rascunhos/${id}/revisao`, { method: "POST", body: JSON.stringify({ versao }) }),
    confirmarEmissao: (emp, id, p) =>
      call(`${e(emp)}/rascunhos/${id}/emissao`, {
        method: "POST",
        headers: { "Idempotency-Key": p.chaveIdempotente },
        body: JSON.stringify({ revisao_id: p.revisaoId, versao: p.versao, ambiente: p.ambiente, confirmacao_humana: true }),
      }, { incerto: true }),
    listarEmissoes: (emp) => call(`${e(emp)}/emissoes`),
    buscarEmissoes: (emp, rid, versao) => call(`${e(emp)}/emissoes?rascunho_id=${encodeURIComponent(rid)}&versao=${versao}`),
    obterEmissao: (emp, id) => call(`${e(emp)}/emissoes/${id}`),
    verificarSituacao: (emp, id) => call(`${e(emp)}/emissoes/${id}/verificar`, { method: "POST" }),
  };
}

interface ApiPrevia {
  layout: string;
  totais: Partial<Record<SituacaoLinha, { qtd: number; valor: string }>>;
  linhas: { linha: number; sistema: string; idOrigem: string; situacao: SituacaoLinha; erros: string[]; dados: LinhaPrevia["dados"] }[];
}

/** Converte a prévia calculada pelo serviço fiscal para o formato da tela. */
export function previaDaApi(r: ApiPrevia): Previa {
  const z = { qtd: 0, valor: "0.00" };
  const t = r.totais;
  return {
    layout: r.layout,
    totais: {
      valida: t.valida ?? z, invalida: t.invalida ?? z, duplicada: t.duplicada ?? z,
      conflito: t.conflito ?? z, repetida_no_arquivo: t.repetida_no_arquivo ?? z,
    },
    linhas: r.linhas.map((l) => ({
      ...l,
      valorCentavos: /^\d+\.\d{2}$/.test(l.dados.valor) ? toCents(l.dados.valor) : 0n,
    })),
  };
}

export const API_URL: string = (import.meta.env["VITE_NFSE_API_URL"] as string | undefined) ?? "";
export const loginUrl = () => `${API_URL.replace(/\/$/, "")}/v1/auth/login?retorno=${encodeURIComponent(typeof window !== "undefined" ? window.location.href : "")}`;
