import { useEffect, useMemo, useRef, useState } from "react";
import { useBlocker, useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useEmpresa } from "./CompanyContext";
import { Notice, StatusBadge } from "./StatusPanel";
import { OPERACAO_LABEL, type DadosRascunho, type Rascunho, type TipoOperacao } from "@/lib/contracts";
import { canonical, dadosVazios, estadoRascunho, formatBRL, formatDoc, liberado, parseMoney, validarDados, type Pendencias } from "@/lib/domain";
import { ConflitoVersao } from "@/lib/datasource";

import { CatalogFields } from "./CatalogFields";

type SaveState = "limpo" | "alterado" | "salvando" | "salvo" | "falha";

function Field({ id, label, erro, hint, children }: { id: string; label: string; erro?: string | undefined; hint?: string | undefined; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {hint && !erro && <p id={`${id}-hint`} className="text-xs text-muted-foreground">{hint}</p>}
      {erro && <p id={`${id}-erro`} className="text-xs font-medium text-destructive">{erro}</p>}
    </div>
  );
}

export function DraftForm({ inicial }: { inicial?: Rascunho }) {
  const { ds, empresa, ambiente, sessao, registrarGuarda } = useEmpresa();
  const nav = useNavigate();
  const qc = useQueryClient();
  const [atual, setAtual] = useState<Rascunho | undefined>(inicial);
  const [dados, setDados] = useState<DadosRascunho>(inicial?.dados ?? dadosVazios());
  const [valorTxt, setValorTxt] = useState(inicial?.dados.valor ? formatBRL(inicial.dados.valor).replace("R$ ", "") : "");
  const [passo, setPasso] = useState(inicial ? 3 : 1);
  const [save, setSave] = useState<SaveState>("limpo");
  const [mostrarErros, setMostrarErros] = useState(false);
  const resumoRef = useRef<HTMLDivElement>(null);
  const base = useRef(canonical(inicial?.dados ?? dadosVazios()));
  const bypass = useRef(false);

  const dirty = canonical(dados) !== base.current;
  useEffect(() => {
    if (dirty && save !== "salvando" && save !== "falha") setSave("alterado");
    if (!dirty && save === "alterado") setSave("limpo");
  }, [dirty]); // eslint-disable-line react-hooks/exhaustive-deps

  const pend: Pendencias = useMemo(() => validarDados(dados, true), [dados]);
  const err = (k: keyof Pendencias) => (mostrarErros ? pend[k] : undefined);
  const lib = liberado(sessao.liberacoes, empresa!.id, dados.operacao, ambiente);

  const set = (patch: Partial<DadosRascunho>) => setDados((d) => ({ ...d, ...patch }));
  const setTom = (patch: Partial<DadosRascunho["tomador"]>) => setDados((d) => ({ ...d, tomador: { ...d.tomador, ...patch } }));

  async function salvar(): Promise<Rascunho | null> {
    setSave("salvando");
    try {
      const r = await ds.salvarRascunho(empresa!.id, {
        id: atual?.id,
        versaoEsperada: atual?.versao,
        dados,
        origem: atual?.origem ?? { tipo: "manual" },
      });
      base.current = canonical(r.dados);
      setAtual(r);
      setSave("salvo");
      qc.invalidateQueries({ queryKey: ["rascunhos", empresa!.id] });
      return r;
    } catch (e) {
      setSave("falha");
      toast.error(e instanceof ConflitoVersao ? e.message : "Não foi possível salvar. Seus dados continuam no formulário.");
      return null;
    }
  }

  // Guarda da troca de empresa (M03)
  const salvarRef = useRef(salvar);
  salvarRef.current = salvar;
  useEffect(() => {
    registrarGuarda({
      dirty,
      save: async () => !!(await salvarRef.current()),
      discard: () => {
        bypass.current = true;
      },
    });
    return () => registrarGuarda(null);
  }, [dirty, registrarGuarda]);

  useBlocker({
    shouldBlockFn: () => {
      if (bypass.current || !dirty) return false;
      return !window.confirm("Há alterações não salvas neste rascunho. Sair e descartar as alterações?");
    },
    enableBeforeUnload: () => dirty && !bypass.current,
  });

  async function onSalvar(ir: "ficar" | "revisar") {
    if (ir === "revisar") {
      setMostrarErros(true);
      if (Object.keys(pend).length) {
        setPasso(3);
        requestAnimationFrame(() => resumoRef.current?.focus());
        return;
      }
    }
    const r = await salvar();
    if (!r) return;
    bypass.current = true;
    if (ir === "revisar") nav({ to: "/revisao/$id", params: { id: r.id } });
    else {
      toast.success("Rascunho salvo — não emitido.");
      if (!inicial) nav({ to: "/rascunho/$id", params: { id: r.id }, replace: true });
      bypass.current = false;
    }
  }

  async function descartar() {
    if (!atual) {
      bypass.current = true;
      nav({ to: "/" });
      return;
    }
    if (!window.confirm("Descartar este rascunho? Ele não foi emitido e será removido.")) return;
    await ds.descartarRascunho(empresa!.id, atual.id);
    qc.invalidateQueries({ queryKey: ["rascunhos", empresa!.id] });
    bypass.current = true;
    toast.success("Rascunho descartado.");
    nav({ to: "/" });
  }

  const passo1Ok = !pend.documento && !pend.nome;
  const passo2Ok = !pend.operacao && !pend.competencia;
  const saveLabel: Record<SaveState, string> = {
    limpo: atual ? "Sem alterações" : "Ainda não salvo",
    alterado: "Alterações não salvas",
    salvando: "Salvando…",
    salvo: "Rascunho salvo — não emitido",
    falha: "Falha ao salvar — dados preservados",
  };
  const pendList = Object.values(pend);

  return (
    <form
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        onSalvar("revisar");
      }}
      className="grid gap-6 lg:grid-cols-[1fr_18rem]"
    >
      <div className="space-y-5">
        {mostrarErros && pendList.length > 0 && (
          <div ref={resumoRef} tabIndex={-1} role="alert" className="rounded-md border border-destructive/30 bg-danger-soft px-4 py-3 text-sm">
            <p className="font-semibold text-destructive">Corrija {pendList.length} {pendList.length === 1 ? "ponto" : "pontos"} antes de revisar:</p>
            <ul className="mt-1 list-disc pl-5">{pendList.map((p) => <li key={p}>{p}</li>)}</ul>
          </div>
        )}

        <fieldset className="surface space-y-4 p-5">
          <legend className="sr-only">Tomador</legend>
          <h2 className="text-sm font-semibold"><span className="mr-2 text-primary">1</span>Tomador do serviço</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field id="doc" label="CPF ou CNPJ" erro={err("documento")}>
              <Input id="doc" inputMode="numeric" className="doc" value={dados.tomador.documento} aria-invalid={!!err("documento")} aria-describedby={err("documento") ? "doc-erro" : undefined}
                onChange={(e) => setTom({ documento: e.target.value })} onBlur={() => setTom({ documento: formatDoc(dados.tomador.documento) })} />
            </Field>
            <Field id="nome" label="Nome ou razão social" erro={err("nome")}>
              <Input id="nome" value={dados.tomador.nome} aria-invalid={!!err("nome")} aria-describedby={err("nome") ? "nome-erro" : undefined} onChange={(e) => setTom({ nome: e.target.value })} />
            </Field>
            <Field id="email" label="E-mail (opcional)">
              <Input id="email" type="email" value={dados.tomador.email ?? ""} onChange={(e) => setTom({ email: e.target.value })} />
            </Field>
          </div>
          {passo === 1 && (
            <Button type="button" variant="secondary" onClick={() => (passo1Ok ? setPasso(2) : setMostrarErros(true))}>Continuar</Button>
          )}
        </fieldset>

        {passo >= 2 && (
          <fieldset className="surface space-y-4 p-5">
            <legend className="sr-only">Operação</legend>
            <h2 className="text-sm font-semibold"><span className="mr-2 text-primary">2</span>Operação</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field id="op" label="Tipo de operação" erro={err("operacao")}>
                <select id="op" className="h-9 w-full rounded-md border border-input bg-card px-3 text-sm" value={dados.operacao} aria-invalid={!!err("operacao")}
                  onChange={(e) => set({ operacao: e.target.value as TipoOperacao })}>
                  <option value="">Selecione…</option>
                  {(Object.keys(OPERACAO_LABEL) as TipoOperacao[]).map((k) => <option key={k} value={k}>{OPERACAO_LABEL[k]}</option>)}
                </select>
              </Field>
              <Field id="comp" label="Competência" erro={err("competencia")}>
                <Input id="comp" type="month" value={dados.competencia} aria-invalid={!!err("competencia")} onChange={(e) => set({ competencia: e.target.value })} />
              </Field>
              <Field id="imovel" label="Imóvel (opcional)" hint="Endereço ou código interno do imóvel">
                <Input id="imovel" value={dados.imovel} onChange={(e) => set({ imovel: e.target.value })} />
              </Field>
            </div>
            {dados.operacao && !lib && (
              <Notice tone="warning" title="Operação não liberada para transmissão">
                {OPERACAO_LABEL[dados.operacao]} não está liberada para {empresa!.razaoSocial} em produção restrita. Você pode salvar o rascunho, mas a transmissão
                ficará bloqueada até o Escritório registrar a liberação com evidência fiscal validada. O sistema não presume regra tributária.
              </Notice>
            )}
            {passo === 2 && (
              <Button type="button" variant="secondary" onClick={() => (passo2Ok ? setPasso(3) : setMostrarErros(true))}>Continuar</Button>
            )}
          </fieldset>
        )}

        {passo >= 2 && <CatalogFields value={dados.fiscal} onChange={(fiscal) => set({ fiscal })} mostrarErros={mostrarErros} />}

        {passo >= 3 && (
          <fieldset className="surface space-y-4 p-5">
            <legend className="sr-only">Valor e descrição</legend>
            <h2 className="text-sm font-semibold"><span className="mr-2 text-primary">3</span>Valor e descrição</h2>
            <Field id="valor" label="Valor do serviço (R$)" erro={err("valor")} hint="Ex.: 1.250,00 — até duas casas decimais">
              <Input id="valor" inputMode="decimal" className="doc max-w-48" value={valorTxt} aria-invalid={!!err("valor")}
                onChange={(e) => {
                  setValorTxt(e.target.value);
                  const m = parseMoney(e.target.value);
                  set({ valor: m.ok ? m.value : e.target.value.trim() ? "x" : "" });
                }} />
            </Field>
            <Field id="desc" label="Descrição do serviço" erro={err("descricao")}>
              <Textarea id="desc" rows={3} value={dados.descricao} aria-invalid={!!err("descricao")} onChange={(e) => set({ descricao: e.target.value })} />
            </Field>
          </fieldset>
        )}
      </div>

      <aside className="space-y-3 lg:sticky lg:top-4 lg:self-start">
        <div className="surface space-y-3 p-4">
          <StatusBadge estado={atual ? estadoRascunho({ ...atual, dados }) === "revisado" && dirty ? "rascunho" : estadoRascunho({ ...atual, dados }) : "rascunho"} />
          <p aria-live="polite" className={save === "falha" ? "text-sm font-medium text-destructive" : "text-sm text-muted-foreground"}>{saveLabel[save]}</p>
          {atual && <p className="text-xs text-muted-foreground">Versão {atual.versao}{atual.origem.tipo === "importacao" ? ` · importado (${atual.origem.idOrigem})` : ""}</p>}
          {atual?.revisao && dirty && <p className="text-xs text-warning-foreground">Alterar dados críticos invalida a revisão anterior.</p>}
          <Button type="submit" className="w-full" disabled={save === "salvando"}>Salvar e revisar</Button>
          <Button type="button" variant="outline" className="w-full" disabled={save === "salvando" || (!dirty && !!atual)} onClick={() => onSalvar("ficar")}>Salvar rascunho</Button>
          <Button type="button" variant="ghost" className="w-full text-destructive" onClick={descartar}>{atual ? "Descartar rascunho" : "Cancelar"}</Button>
        </div>
        <p className="px-1 text-xs text-muted-foreground">Salvar não transmite nada. A emissão só acontece após a revisão final e sua confirmação.</p>
      </aside>
    </form>
  );
}
