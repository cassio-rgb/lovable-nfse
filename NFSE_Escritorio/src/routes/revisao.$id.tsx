import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { AccessDenied } from "@/components/AccessDenied";
import { Notice } from "@/components/StatusPanel";
import { useEmpresa } from "@/components/CompanyContext";
import { OPERACAO_LABEL, type Cenario, type Rascunho } from "@/lib/contracts";
import { formatBRL, formatDoc, liberado, revisaoValida } from "@/lib/domain";
import { AcessoNegado } from "@/lib/datasource";
import { chaveEstavel, confirmar, type ResultadoConfirmacao } from "@/lib/confirm";
import { fmtComp, useRascunho } from "@/lib/hooks";

import { CatalogSummary } from "@/components/CatalogFields";

export const Route = createFileRoute("/revisao/$id")({
  head: () => ({
    meta: [
      { title: "Revisão final — NFS-e Imóveis" },
      { name: "description", content: "Confira empresa, tomador, operação e valor antes da transmissão." },
      { property: "og:title", content: "Revisão final — NFS-e Imóveis" },
      { property: "og:description", content: "Confira empresa, tomador, operação e valor antes da transmissão." },
    ],
  }),
  component: Page,
});

function Row({ k, v, mono }: { k: string; v: React.ReactNode; mono?: boolean }) {
  return (
    <div className="grid gap-1 py-2.5 sm:grid-cols-[12rem_1fr]">
      <dt className="text-sm text-muted-foreground">{k}</dt>
      <dd className={mono ? "doc text-sm font-medium" : "text-sm font-medium"}>{v}</dd>
    </div>
  );
}

function Page() {
  const { id } = Route.useParams();
  const { ds, empresa, ambiente, sessao } = useEmpresa();
  const q = useRascunho(id);
  const qc = useQueryClient();
  const nav = useNavigate();
  const [rev, setRev] = useState<Rascunho | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [conferi, setConferi] = useState(false);
  const [cenario, setCenario] = useState<Cenario>("aceita");

  const preparar = useMutation({
    mutationFn: (r: Rascunho) => ds.prepararRevisao(empresa!.id, r.id, r.versao),
    onSuccess: setRev,
    onError: (e) => setErro(e.message),
  });
  useEffect(() => {
    if (q.data && !q.data.emissaoId && !rev && !preparar.isPending && !erro) preparar.mutate(q.data);
  }, [q.data]); // eslint-disable-line react-hooks/exhaustive-deps

  const [tentou, setTentou] = useState(false);
  const [res, setRes] = useState<ResultadoConfirmacao | null>(null);
  const emitir = useMutation({
    mutationFn: async (): Promise<ResultadoConfirmacao> => {
      if (!rev?.revisao) return { tipo: "conflito" };
      const params = {
        empresaId: empresa!.id, rascunhoId: id, revisaoId: rev.revisao.id, versao: rev.versao, ambiente,
        chave: chaveEstavel(empresa!.id, id, rev.versao, ambiente, rev.revisao.hash),
        cenario: ds.modo === "demo" ? cenario : undefined,
      };
      if (!tentou) {
        // Revalida a versão atual antes da primeira confirmação (outra aba pode ter alterado).
        const atual = await ds.obterRascunho(empresa!.id, id).catch(() => null);
        if (atual && (atual.versao !== rev.versao || (!atual.emissaoId && !revisaoValida(atual)))) return { tipo: "conflito" };
      }
      setTentou(true);
      return confirmar(ds, params, { jaTentou: tentou });
    },
    onSuccess: (r) => {
      setRes(r);
      if (r.tipo === "bloqueio" || r.tipo === "conflito") setTentou(false);
      if (r.tipo === "ok") {
        qc.invalidateQueries({ queryKey: ["emissoes", empresa!.id] });
        qc.invalidateQueries({ queryKey: ["rascunhos", empresa!.id] });
        nav({ to: "/operacao/$id", params: { id: r.emissao.id } });
      }
    },
    onError: () => setRes({ tipo: "incerto" }),
  });

  if (q.isLoading) return <p role="status" className="text-sm text-muted-foreground">Carregando…</p>;
  if (q.error instanceof AcessoNegado) return <AccessDenied />;
  if (q.isError) return <p role="alert" className="text-destructive">Falha ao carregar.</p>;
  const r = q.data!;
  if (r.emissaoId)
    return (
      <Notice tone="info" title="Este rascunho já foi enviado">
        <Link className="font-medium text-primary underline" to="/operacao/$id" params={{ id: r.emissaoId }}>Acompanhar o envio</Link>. Um novo envio não é permitido.
      </Notice>
    );

  const lib = liberado(sessao.liberacoes, empresa!.id, r.dados.operacao, ambiente);
  const stale = res?.tipo === "conflito";
  const incerto = res?.tipo === "incerto";
  const demo = ds.modo === "demo";
  const d = rev?.dados ?? r.dados;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Revisão final</h1>
        <p className="mt-1 text-sm text-muted-foreground">Confira os dados críticos. Qualquer alteração depois desta revisão exige nova revisão.</p>
      </div>

      {erro && (
        <Notice tone="danger" title="Não foi possível preparar a revisão">
          {erro} <Link className="font-medium underline" to="/rascunho/$id" params={{ id }}>Voltar e corrigir</Link>
        </Notice>
      )}
      {stale && (
        <Notice tone="warning" title="A versão do rascunho mudou">
          Os dados foram alterados depois desta revisão (por exemplo, em outra janela). Nada foi enviado.{" "}
          <button className="font-medium underline" onClick={() => { setRev(null); setErro(null); setRes(null); setTentou(false); emitir.reset(); q.refetch().then((x) => x.data && preparar.mutate(x.data)); }}>
            Revisar a versão atual
          </button>
        </Notice>
      )}
      {incerto && (
        <Notice tone="warning" title="Resultado da confirmação desconhecido">
          A resposta não chegou. A confirmação pode ter sido registrada e a nota pode estar em processamento. Não repita a emissão:
          verifique a situação. A verificação consulta primeiro se a operação já existe e reutiliza a mesma chave desta revisão,
          o que impede uma segunda operação.
          <div className="mt-3">
            <Button size="sm" disabled={emitir.isPending} onClick={() => emitir.mutate()}>
              {emitir.isPending ? "Consultando…" : "Verificar situação"}
            </Button>
          </div>
        </Notice>
      )}
      {res?.tipo === "bloqueio" && <Notice tone="danger" title="Confirmação recusada pelo serviço">{res.mensagem}</Notice>}

      <section aria-labelledby="emp-h" className="surface p-5">
        <h2 id="emp-h" className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Prestador (empresa ativa)</h2>
        <dl className="mt-2 divide-y">
          <Row k="Razão social" v={empresa!.razaoSocial} />
          <Row k="CNPJ" v={empresa!.cnpj} mono />
          <Row k="Município" v={empresa!.municipio} />
          <Row k="Ambiente" v="Produção restrita (homologação)" />
        </dl>
      </section>
      <section aria-labelledby="tom-h" className="surface p-5">
        <h2 id="tom-h" className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Tomador e serviço</h2>
        <dl className="mt-2 divide-y">
          <Row k="Tomador" v={d.tomador.nome} />
          <Row k="CPF/CNPJ" v={formatDoc(d.tomador.documento)} mono />
          <Row k="Operação" v={d.operacao ? OPERACAO_LABEL[d.operacao] : "—"} />
          <Row k="Competência" v={fmtComp(d.competencia)} />
          <Row k="Imóvel" v={d.imovel || "—"} />
          <Row k="Descrição" v={d.descricao} />
          <Row k="Valor" v={<span className="text-lg">{formatBRL(d.valor)}</span>} mono />
        </dl>
        {rev?.revisao && <p className="mt-3 text-xs text-muted-foreground">Revisão da versão {rev.versao} · código <span className="doc">{rev.revisao.hash}</span></p>}
      </section>

      <CatalogSummary value={d.fiscal} />

      {!lib ? (
        <Notice tone="warning" title="Transmissão bloqueada: operação não liberada">
          Esta operação não está liberada para esta empresa em produção restrita. Próximo passo: o Escritório deve registrar a liberação
          (empresa, operação, município e ambiente) com evidência fiscal validada. O rascunho continua salvo.
        </Notice>
      ) : (
        <section className="surface space-y-4 p-5">
          {demo && (
            <fieldset className="space-y-2">
              <legend className="text-sm font-semibold">Simulação — cenário de retorno</legend>
              <p className="text-xs text-muted-foreground">Modo demonstração: nada é enviado à NFS-e Nacional. Escolha o retorno a simular.</p>
              <div className="flex flex-wrap gap-4 text-sm">
                {([["aceita", "Aceita"], ["rejeitada", "Rejeição de negócio"], ["desconhecido", "Resposta perdida (resultado desconhecido)"]] as const).map(([v, l]) => (
                  <label key={v} className="flex items-center gap-2">
                    <input type="radio" name="cenario" value={v} checked={cenario === v} onChange={() => setCenario(v)} /> {l}
                  </label>
                ))}
              </div>
            </fieldset>
          )}
          <div className="flex items-start gap-2">
            <Checkbox id="conferi" checked={conferi} onCheckedChange={(v) => setConferi(v === true)} />
            <Label htmlFor="conferi" className="text-sm font-normal leading-snug">
              Conferi empresa, CNPJ, tomador, operação, valor e códigos fiscais, e confirmo {demo ? "a simulação do envio" : "a emissão desta NFS-e"}.
            </Label>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button disabled={!conferi || !rev || !revisaoValida(rev) || !rev?.revisao || emitir.isPending || stale || incerto || tentou} onClick={() => emitir.mutate()}>
              {emitir.isPending ? "Enviando…" : demo ? "Executar simulação de envio" : "Emitir NFS-e"}
            </Button>
            <Button asChild variant="outline"><Link to="/rascunho/$id" params={{ id }}>Voltar e corrigir</Link></Button>
          </div>
        </section>
      )}
      {!lib && <Button asChild variant="outline"><Link to="/rascunho/$id" params={{ id }}>Voltar ao rascunho</Link></Button>}
    </div>
  );
}
