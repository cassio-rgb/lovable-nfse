import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { AccessDenied } from "@/components/AccessDenied";
import { Notice, StatusBadge } from "@/components/StatusPanel";
import { useEmpresa } from "@/components/CompanyContext";
import { OPERACAO_LABEL } from "@/lib/contracts";
import { formatBRL, formatDoc } from "@/lib/domain";
import { AcessoNegado, API_URL } from "@/lib/datasource";
import { fmtComp, fmtData } from "@/lib/hooks";

export const Route = createFileRoute("/operacao/$id")({
  head: () => ({
    meta: [
      { title: "Acompanhamento — NFS-e Imóveis" },
      { name: "description", content: "Situação persistida do envio e resultado da NFS-e." },
      { property: "og:title", content: "Acompanhamento — NFS-e Imóveis" },
      { property: "og:description", content: "Situação persistida do envio e resultado da NFS-e." },
    ],
  }),
  component: Page,
});

function Page() {
  const { id } = Route.useParams();
  const { ds, empresa } = useEmpresa();
  const qc = useQueryClient();
  const nav = useNavigate();
  const q = useQuery({
    queryKey: ["emissao", empresa!.id, id],
    queryFn: () => ds.obterEmissao(empresa!.id, id),
    retry: false,
    refetchInterval: (s) => (s.state.data && ["na_fila", "transmitindo"].includes(s.state.data.estado) ? 1000 : false),
  });
  const verificar = useMutation({
    mutationFn: () => ds.verificarSituacao(empresa!.id, id),
    onSuccess: (e) => {
      qc.setQueryData(["emissao", empresa!.id, id], e);
      qc.invalidateQueries({ queryKey: ["emissoes", empresa!.id] });
    },
  });
  const corrigir = useMutation({
    mutationFn: () => ds.salvarRascunho(empresa!.id, { dados: q.data!.snapshot, origem: { tipo: "manual" } }),
    onSuccess: (r) => nav({ to: "/rascunho/$id", params: { id: r.id } }),
  });

  if (q.isLoading) return <p role="status" className="text-sm text-muted-foreground">Carregando…</p>;
  if (q.error instanceof AcessoNegado) return <AccessDenied />;
  if (q.isError) return <p role="alert" className="text-destructive">Falha ao consultar a situação. <button className="underline" onClick={() => q.refetch()}>Tentar novamente</button> (consultar não reenvia).</p>;
  const e = q.data!;
  const s = e.snapshot;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold">{e.simulacao ? "Simulação de envio" : "Acompanhamento da NFS-e"}</h1>
        <StatusBadge estado={e.estado} simulacao={e.simulacao} />
      </div>

      <div aria-live="polite">
        {(e.estado === "na_fila" || e.estado === "transmitindo") && (
          <Notice title={e.estado === "na_fila" ? "Na fila de transmissão" : "Transmitindo"}>
            O envio está em andamento. Você pode fechar esta página; a situação fica registrada e um novo envio não será criado.
          </Notice>
        )}
        {e.estado === "resultado_desconhecido" && (
          <Notice tone="warning" title="Resultado desconhecido">
            A resposta do envio não foi confirmada. A nota pode ter sido emitida. Não reenvie: verifique a situação pela identidade da DPS{" "}
            <span className="doc">{e.identidadeDps}</span>. Se persistir, informe ao suporte o código de atendimento <span className="doc">{e.id}</span>.
            <div className="mt-3">
              <Button size="sm" disabled={verificar.isPending} onClick={() => verificar.mutate()}>
                {verificar.isPending ? "Consultando…" : e.simulacao ? "Verificar situação (simulação)" : "Verificar situação"}
              </Button>
              {verificar.isError && <p role="alert" className="mt-2 text-destructive">A consulta falhou. Nada foi reenviado; tente verificar novamente.</p>}
            </div>
          </Notice>
        )}
        {e.estado === "emitida" && (
          <Notice tone="success" title={e.simulacao ? "Simulação: aceita — nenhuma NFS-e foi emitida" : "NFS-e emitida"}>
            {e.retorno?.mensagem}
          </Notice>
        )}
        {e.estado === "rejeitada" && (
          <Notice tone="danger" title={e.simulacao ? "Simulação: rejeitada" : "NFS-e rejeitada"}>
            <p>{e.retorno?.mensagem}</p>
            <details className="mt-2 text-xs">
              <summary className="cursor-pointer">Detalhe técnico</summary>
              <p className="doc mt-1">{e.retorno?.codigo} — {e.retorno?.detalheTecnico}</p>
            </details>
            <Button size="sm" className="mt-3" disabled={corrigir.isPending} onClick={() => corrigir.mutate()}>Corrigir em novo rascunho</Button>
          </Notice>
        )}
      </div>

      <section className="surface p-5 text-sm">
        <dl className="grid gap-3 sm:grid-cols-2">
          <div><dt className="text-muted-foreground">Prestador</dt><dd className="font-medium">{empresa!.razaoSocial} · <span className="doc">{empresa!.cnpj}</span></dd></div>
          <div><dt className="text-muted-foreground">Tomador</dt><dd className="font-medium">{s.tomador.nome} · <span className="doc">{formatDoc(s.tomador.documento)}</span></dd></div>
          <div><dt className="text-muted-foreground">Operação</dt><dd>{s.operacao ? OPERACAO_LABEL[s.operacao] : "—"} · comp. {fmtComp(s.competencia)}</dd></div>
          <div><dt className="text-muted-foreground">Valor</dt><dd className="doc font-medium">{formatBRL(s.valor)}</dd></div>
          <div><dt className="text-muted-foreground">Identidade da DPS</dt><dd className="doc">{e.identidadeDps}</dd></div>
          <div><dt className="text-muted-foreground">Registrado em</dt><dd>{fmtData(e.criadoEm)}</dd></div>
          {e.retorno?.numero && <div><dt className="text-muted-foreground">{e.simulacao ? "Número simulado" : "Número da NFS-e"}</dt><dd className="doc">{e.retorno.numero}</dd></div>}
          {e.retorno?.chave && <div className="sm:col-span-2"><dt className="text-muted-foreground">{e.simulacao ? "Chave simulada" : "Chave de acesso"}</dt><dd className="doc break-all">{e.retorno.chave}</dd></div>}
        </dl>
        {e.estado === "emitida" && (
          <div className="mt-4 border-t pt-4">
            {e.simulacao ? (
              <p className="text-muted-foreground">Em simulação não existe documento fiscal para visualizar. O documento oficial só existe após emissão real pelo serviço fiscal.</p>
            ) : (
              <Button asChild variant="outline">
                <a href={`${API_URL.replace(/\/$/, "")}/v1/empresas/${empresa!.id}/emissoes/${e.id}/documento`} target="_blank" rel="noreferrer">Visualizar documento</a>
              </Button>
            )}
          </div>
        )}
      </section>
      <Link to="/historico" className="text-sm text-primary underline-offset-4 hover:underline">Voltar ao histórico</Link>
    </div>
  );
}
