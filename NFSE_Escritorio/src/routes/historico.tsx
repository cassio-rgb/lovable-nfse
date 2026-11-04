import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { StatusBadge } from "@/components/StatusPanel";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ESTADO_LABEL, type EstadoFiscal } from "@/lib/contracts";
import { formatBRL, onlyDigits } from "@/lib/domain";
import { fmtComp, fmtData, useEmissoes } from "@/lib/hooks";

export const Route = createFileRoute("/historico")({
  head: () => ({
    meta: [
      { title: "Histórico — NFS-e Imóveis" },
      { name: "description", content: "Histórico de envios de NFS-e da empresa ativa, com situação de cada operação." },
      { property: "og:title", content: "Histórico — NFS-e Imóveis" },
      { property: "og:description", content: "Histórico de envios de NFS-e da empresa ativa, com situação de cada operação." },
    ],
  }),
  component: Page,
});

function Page() {
  const q = useEmissoes(3000);
  const [busca, setBusca] = useState("");
  const [estado, setEstado] = useState<EstadoFiscal | "">("");
  const lista = (q.data ?? []).filter((e) => {
    const b = busca.trim().toLowerCase();
    const okB = !b || e.snapshot.tomador.nome.toLowerCase().includes(b) || (onlyDigits(b) && onlyDigits(e.snapshot.tomador.documento).includes(onlyDigits(b)));
    return okB && (!estado || e.estado === estado);
  });
  const filtrando = !!busca || !!estado;
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Histórico</h1>
      <div className="flex flex-wrap gap-3">
        <Input aria-label="Buscar por tomador ou CPF/CNPJ" placeholder="Tomador ou CPF/CNPJ" className="max-w-xs bg-card" value={busca} onChange={(e) => setBusca(e.target.value)} />
        <select aria-label="Filtrar por situação" className="h-9 w-full min-w-0 max-w-full rounded-md border border-input bg-card px-3 text-sm sm:w-auto" value={estado} onChange={(e) => setEstado(e.target.value as EstadoFiscal | "")}>
          <option value="">Todas as situações</option>
          {(["na_fila", "transmitindo", "resultado_desconhecido", "emitida", "rejeitada", "erro_pre_envio"] as EstadoFiscal[]).map((s) => <option key={s} value={s}>{ESTADO_LABEL[s]}</option>)}
        </select>
        {filtrando && <Button variant="ghost" onClick={() => { setBusca(""); setEstado(""); }}>Limpar filtros</Button>}
      </div>
      {q.isLoading ? (
        <p role="status" className="text-sm text-muted-foreground">Carregando…</p>
      ) : q.isError ? (
        <p role="alert" className="text-sm text-destructive">Não foi possível carregar. <button className="underline" onClick={() => q.refetch()}>Tentar novamente</button></p>
      ) : !lista.length ? (
        <p className="surface px-4 py-8 text-center text-sm text-muted-foreground">{filtrando ? "Nenhum envio corresponde aos filtros." : "Nenhum envio registrado para esta empresa."}</p>
      ) : (
        <ul className="surface divide-y">
          {lista.map((e) => (
            <li key={e.id}>
              <Link to="/operacao/$id" params={{ id: e.id }} className="grid gap-1 px-4 py-3 text-sm hover:bg-muted/60 sm:grid-cols-[1fr_8rem_7rem_9rem_auto] sm:items-center sm:gap-4">
                <span className="font-medium">{e.snapshot.tomador.nome}</span>
                <span className="doc">{formatBRL(e.snapshot.valor)}</span>
                <span className="text-muted-foreground">Comp. {fmtComp(e.snapshot.competencia)}</span>
                <span className="text-muted-foreground">{fmtData(e.criadoEm)}</span>
                <StatusBadge estado={e.estado} simulacao={e.simulacao} />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
