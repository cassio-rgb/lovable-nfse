import { createFileRoute, Link } from "@tanstack/react-router";
import { DraftForm } from "@/components/DraftForm";
import { AccessDenied } from "@/components/AccessDenied";
import { useRascunho } from "@/lib/hooks";
import { AcessoNegado } from "@/lib/datasource";

export const Route = createFileRoute("/rascunho/$id")({
  head: () => ({
    meta: [
      { title: "Rascunho — NFS-e Imóveis" },
      { name: "description", content: "Edite um rascunho de NFS-e ainda não emitido." },
      { property: "og:title", content: "Rascunho — NFS-e Imóveis" },
      { property: "og:description", content: "Edite um rascunho de NFS-e ainda não emitido." },
    ],
  }),
  component: Page,
});

function Page() {
  const { id } = Route.useParams();
  const q = useRascunho(id);
  if (q.isLoading) return <p role="status" className="text-sm text-muted-foreground">Carregando…</p>;
  if (q.error instanceof AcessoNegado) return <AccessDenied />;
  if (q.isError) return <p role="alert" className="text-destructive">Falha ao carregar. <button className="underline" onClick={() => q.refetch()}>Tentar novamente</button></p>;
  const r = q.data!;
  if (r.emissaoId)
    return (
      <div className="surface p-6 text-sm">
        Este rascunho já foi enviado e não pode ser alterado. <Link className="font-medium text-primary underline" to="/operacao/$id" params={{ id: r.emissaoId }}>Acompanhar envio</Link>
      </div>
    );
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Editar rascunho</h1>
      <DraftForm key={r.id} inicial={r} />
    </div>
  );
}
