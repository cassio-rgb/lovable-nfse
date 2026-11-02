import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { useEmpresa } from "./CompanyContext";
import { Notice } from "./StatusPanel";
import { OPERACAO_LABEL } from "@/lib/contracts";
import { formatBRL, fromCents } from "@/lib/domain";
import { chaveOrigem, MAX_BYTES, MODELO_CSV, type Previa, type SituacaoLinha } from "@/lib/imports";

const SIT: Record<SituacaoLinha, { label: string; cls: string }> = {
  valida: { label: "Válida", cls: "bg-success-soft text-success" },
  invalida: { label: "Inválida", cls: "bg-danger-soft text-destructive" },
  duplicada: { label: "Já importada", cls: "bg-muted text-muted-foreground" },
  conflito: { label: "Conflito com importação anterior", cls: "bg-warning-soft text-warning-foreground" },
  repetida_no_arquivo: { label: "Repetida no arquivo", cls: "bg-warning-soft text-warning-foreground" },
};

export function ImportPreview() {
  const { ds, empresa } = useEmpresa();
  const qc = useQueryClient();
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [previa, setPrevia] = useState<Previa | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [sel, setSel] = useState<Set<number>>(new Set());
  const [busy, setBusy] = useState(false);
  const [inputKey, setInputKey] = useState(0);
  const [resultado, setResultado] = useState<{ criados: number; ignorados: number } | null>(null);

  async function analisarArquivo() {
    if (!arquivo) return setErro("Selecione um arquivo .csv ou .xlsx.");
    if (arquivo.size > MAX_BYTES) return setErro("Arquivo maior que 5 MiB.");
    setBusy(true); setErro(null); setResultado(null);
    try {
      // Modo API: a prévia é calculada pelo serviço fiscal (autoridade). Demonstração: localmente.
      const p = await ds.analisarImportacao(empresa!.id, arquivo);
      if (p.erroArquivo) { setErro(p.erroArquivo); setPrevia(null); }
      else { setPrevia(p); setSel(new Set(p.linhas.filter((l) => l.situacao === "valida").map((l) => l.linha))); }
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não foi possível ler o arquivo.");
    } finally { setBusy(false); }
  }

  async function confirmar() {
    if (!previa) return;
    setBusy(true);
    try {
      // Reanalisa contra o estado atual para não duplicar se outra janela importou antes.
      const imp = await ds.importados(empresa!.id);
      const linhas = previa.linhas.filter((l) => sel.has(l.linha) && l.situacao === "valida" && !imp.has(chaveOrigem(l.sistema, l.idOrigem)));
      const r = await ds.confirmarImportacao(empresa!.id, linhas);
      const ign = r.ignorados + (sel.size - linhas.length);
      setResultado({ criados: r.criados, ignorados: ign });
      qc.invalidateQueries({ queryKey: ["rascunhos", empresa!.id] });
      setPrevia(null); setArquivo(null); setInputKey((k) => k + 1);
      toast.success(`${r.criados} rascunho(s) criado(s) — nenhum emitido.`);
    } catch {
      setErro("Falha ao confirmar a importação. Nenhum rascunho foi criado; tente novamente.");
    } finally { setBusy(false); }
  }

  const baixarModelo = () => {
    const url = URL.createObjectURL(new Blob(["\uFEFF" + MODELO_CSV], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = "modelo-nfse-imoveis.csv"; a.click(); URL.revokeObjectURL(url);
  };

  const selValor = previa ? fromCents(previa.linhas.filter((l) => sel.has(l.linha)).reduce((s, l) => s + l.valorCentavos, 0n)) : "0.00";

  return (
    <div className="space-y-6">
      <section className="surface space-y-4 p-5">
        <p className="text-sm">Destino: <strong>{empresa!.razaoSocial}</strong> · <span className="doc">{empresa!.cnpj}</span></p>
        <p className="text-sm text-muted-foreground">
          Layout <span className="doc">nfse-imoveis-v1</span>. A coluna <span className="doc">id_origem</span> é obrigatória e identifica cada registro para que
          reimportações não dupliquem rascunhos. Fórmulas não são executadas. Importar não emite notas.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <label htmlFor="arq" className="sr-only">Arquivo CSV ou XLSX</label>
          <input key={inputKey} id="arq" type="file" accept=".csv,.xlsx" className="text-sm file:mr-3 file:rounded-md file:border file:border-input file:bg-card file:px-3 file:py-1.5 file:text-sm"
            onChange={(e) => { setArquivo(e.target.files?.[0] ?? null); setPrevia(null); setErro(null); }} />
          <Button onClick={analisarArquivo} disabled={busy || !arquivo}>{busy && !previa ? "Analisando…" : "Analisar arquivo"}</Button>
          <Button variant="ghost" onClick={baixarModelo}>Baixar modelo CSV</Button>
        </div>
        {erro && <Notice tone="danger" title="Não foi possível continuar">{erro}</Notice>}
        {resultado && (
          <Notice tone="success" title={`${resultado.criados} rascunho(s) criado(s) — não emitidos`}>
            {resultado.ignorados > 0 && `${resultado.ignorados} linha(s) não importada(s). `}
            <Link to="/" className="font-medium underline">Ver rascunhos</Link>
          </Notice>
        )}
      </section>

      {previa && (
        <section aria-labelledby="prev-h" className="space-y-4">
          <h2 id="prev-h" className="text-lg font-semibold">Prévia da importação</h2>
          <dl className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {(Object.keys(SIT) as SituacaoLinha[]).map((k) => (
              <div key={k} className="surface p-3">
                <dt className="text-xs text-muted-foreground">{SIT[k].label}</dt>
                <dd className="mt-1 text-lg font-semibold">{previa.totais[k].qtd}</dd>
                <dd className="doc text-xs text-muted-foreground">{formatBRL(previa.totais[k].valor)}</dd>
              </div>
            ))}
          </dl>
          <div className="surface overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/60 text-left text-xs text-muted-foreground">
                <tr>
                  <th className="px-3 py-2"><span className="sr-only">Selecionar</span></th>
                  <th className="px-3 py-2">Linha</th><th className="px-3 py-2">id_origem</th><th className="px-3 py-2">Tomador</th>
                  <th className="px-3 py-2">Operação</th><th className="px-3 py-2 text-right">Valor</th><th className="px-3 py-2">Situação</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {previa.linhas.map((l) => (
                  <tr key={l.linha} className="align-top">
                    <td className="px-3 py-2">
                      <Checkbox aria-label={`Selecionar linha ${l.linha}`} disabled={l.situacao !== "valida"} checked={sel.has(l.linha)}
                        onCheckedChange={(v) => setSel((s) => { const n = new Set(s); if (v) n.add(l.linha); else n.delete(l.linha); return n; })} />
                    </td>
                    <td className="px-3 py-2 doc">{l.linha}</td>
                    <td className="px-3 py-2 doc">{l.idOrigem || "—"}</td>
                    <td className="px-3 py-2">{l.dados.tomador.nome || "—"}</td>
                    <td className="px-3 py-2">{l.dados.operacao ? OPERACAO_LABEL[l.dados.operacao] : "—"}</td>
                    <td className="px-3 py-2 doc text-right">{l.dados.valor ? formatBRL(l.dados.valor) : "—"}</td>
                    <td className="px-3 py-2">
                      <span className={`rounded px-2 py-0.5 text-xs font-medium ${SIT[l.situacao].cls}`}>{SIT[l.situacao].label}</span>
                      {l.erros.length > 0 && <ul className="mt-1 list-disc pl-4 text-xs text-destructive">{l.erros.map((e) => <li key={e}>{e}</li>)}</ul>}
                      {l.situacao === "conflito" && <p className="mt-1 text-xs text-muted-foreground">O conteúdo mudou desde a importação anterior; o rascunho existente não será sobrescrito.</p>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="surface flex flex-wrap items-center gap-3 p-4">
            <p className="mr-auto text-sm">
              Serão criados <strong>{sel.size}</strong> rascunho(s), total <span className="doc font-semibold">{formatBRL(selValor)}</span>. Linhas inválidas, duplicadas e em conflito ficam de fora.
            </p>
            <Button variant="outline" onClick={() => setPrevia(null)} disabled={busy}>Cancelar</Button>
            <Button onClick={confirmar} disabled={busy || sel.size === 0}>{busy ? "Criando…" : `Criar ${sel.size} rascunho(s)`}</Button>
          </div>
        </section>
      )}
    </div>
  );
}
