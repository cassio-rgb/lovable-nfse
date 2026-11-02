import { createFileRoute } from "@tanstack/react-router";
import { DraftForm } from "@/components/DraftForm";

export const Route = createFileRoute("/nova")({
  head: () => ({
    meta: [
      { title: "Nova NFS-e — NFS-e Imóveis" },
      { name: "description", content: "Preencha tomador, operação e valor para criar um rascunho de NFS-e." },
      { property: "og:title", content: "Nova NFS-e — NFS-e Imóveis" },
      { property: "og:description", content: "Preencha tomador, operação e valor para criar um rascunho de NFS-e." },
    ],
  }),
  component: () => (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Nova NFS-e</h1>
      <DraftForm />
    </div>
  ),
});
