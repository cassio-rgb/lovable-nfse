import { createFileRoute } from "@tanstack/react-router";
import { ImportPreview } from "@/components/ImportPreview";

export const Route = createFileRoute("/importar")({
  head: () => ({
    meta: [
      { title: "Importar planilha — NFS-e Imóveis" },
      { name: "description", content: "Importe CSV ou XLSX, confira a prévia por linha e crie rascunhos de NFS-e." },
      { property: "og:title", content: "Importar planilha — NFS-e Imóveis" },
      { property: "og:description", content: "Importe CSV ou XLSX, confira a prévia por linha e crie rascunhos de NFS-e." },
    ],
  }),
  component: () => (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Importar planilha</h1>
      <ImportPreview />
    </div>
  ),
});
