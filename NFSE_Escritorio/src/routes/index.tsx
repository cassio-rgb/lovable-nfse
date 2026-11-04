import { createFileRoute, Link } from "@tanstack/react-router";
import { FilePlus2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/StatusPanel";
import { useEmpresa } from "@/components/CompanyContext";
import { estadoRascunho, formatBRL } from "@/lib/domain";
import { fmtComp, fmtData, useEmissoes, useRascunhos } from "@/lib/hooks";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Início — NFS-e Imóveis" },
      { name: "description", content: "Rascunhos, pendências e emissões recentes de NFS-e da empresa ativa." },
      { property: "og:title", content: "Início — NFS-e Imóveis" },
      { property: "og:description", content: "Rascunhos, pendências e emissões recentes de NFS-e da empresa ativa." },
    ],
  }),
  component: Inicio,
});

function Inicio() {
  const { empresa } = useEmpresa();
  const r = useRascunhos();
  const e = useEmissoes();
  const pend = (e.data ?? []).filter((x) => x.estado === "resultado_desconhecido" || x.estado === "rejeitada" || x.estado === "erro_pre_envio");
  const recentes = (e.data ?? []).slice(0, 5);
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{empresa!.razaoSocial}</h1>
          <p className="mt-1 text-sm text-muted-foreground">Prepare, revise e acompanhe as NFS-e desta empresa.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline"><Link to="/importar"><Upload aria-hidden /> Importar planilha</Link></Button>
          <Button asChild><Link to="/nova"><FilePlus2 aria-hidden /> Nova NFS-e</Link></Button>
        </div>
      </div>

      {pend.length > 0 && (
        <section aria-labelledby="pend-h" className="space-y-2">
          <h2 id="pend-h" className="text-sm font-semibold">Pendências</h2>
          <ul className="surface divide-y">
            {pend.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center gap-3 px-4 py-3 text-sm">
                <StatusBadge estado={p.estado} simulacao={p.simulacao} />
                <span className="font-medium">{p.snapshot.tomador.nome}</span>
                <span className="doc">{formatBRL(p.snapshot.valor)}</span>
                <Link className="ml-auto font-medium text-primary underline-offset-4 hover:underline" to="/operacao/$id" params={{ id: p.id }}>
                  {p.estado === "resultado_desconhecido" ? "Verificar situação" : "Ver detalhes"}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section aria-labelledby="rasc-h" className="space-y-2">
        <h2 id="rasc-h" className="text-sm font-semibold">Rascunhos <span className="font-normal text-muted-foreground">— não emitidos</span></h2>
        {r.isLoading ? (
          <p className="text-sm text-muted-foreground" role="status">Carregando rascunhos…</p>
        ) : r.isError ? (
          <p role="alert" className="text-sm text-destructive">Não foi possível carregar os rascunhos. <button className="underline" onClick={() => r.refetch()}>Tentar novamente</button></p>
        ) : !r.data?.length ? (
          <div className="surface px-4 py-8 text-center text-sm text-muted-foreground">
            Nenhum rascunho. Comece por <Link to="/nova" className="font-medium text-primary underline">Nova NFS-e</Link> ou importe uma planilha.
          </div>
        ) : (
          <ul className="surface divide-y">
            {r.data.map((d) => (
              <li key={d.id}>
                <Link to="/rascunho/$id" params={{ id: d.id }} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 text-sm hover:bg-muted/60">
                  <span className="min-w-48 font-medium">{d.dados.tomador.nome || "Tomador não informado"}</span>
                  <span className="text-muted-foreground">Comp. {fmtComp(d.dados.competencia)}</span>
                  <span className="doc">{d.dados.valor && d.dados.valor !== "x" ? formatBRL(d.dados.valor) : "—"}</span>
                  {d.origem.tipo === "importacao" && <span className="text-xs text-muted-foreground">Importado · {d.origem.idOrigem}</span>}
                  <span className="ml-auto"><StatusBadge estado={estadoRascunho(d)} /></span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="rec-h" className="space-y-2">
        <div className="flex items-center justify-between">
          <h2 id="rec-h" className="text-sm font-semibold">Envios recentes</h2>
          <Link to="/historico" className="text-sm text-primary underline-offset-4 hover:underline">Ver histórico</Link>
        </div>
        {!recentes.length ? (
          <p className="surface px-4 py-6 text-center text-sm text-muted-foreground">Nenhum envio ainda.</p>
        ) : (
          <ul className="surface divide-y">
            {recentes.map((x) => (
              <li key={x.id}>
                <Link to="/operacao/$id" params={{ id: x.id }} className="flex flex-wrap items-center gap-4 px-4 py-3 text-sm hover:bg-muted/60">
                  <span className="min-w-48 font-medium">{x.snapshot.tomador.nome}</span>
                  <span className="doc">{formatBRL(x.snapshot.valor)}</span>
                  <span className="text-muted-foreground">{fmtData(x.criadoEm)}</span>
                  <span className="ml-auto"><StatusBadge estado={x.estado} simulacao={x.simulacao} /></span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
