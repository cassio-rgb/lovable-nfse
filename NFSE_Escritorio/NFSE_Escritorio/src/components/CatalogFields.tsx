import { useId, useState } from "react";
import type { SelecaoFiscal } from "@/lib/contracts";
import {
  catalogo,
  classesNFSe,
  csts,
  fiscalLinhas,
  fiscalVazio,
  indopsNFSe,
  nbsDisponiveis,
  pesquisar,
  validarCatalogo,
  type OpcaoFiscal,
} from "@/lib/catalogos";

function Busca({
  label,
  options,
  value,
  onChange,
  erro,
}: {
  label: string;
  options: OpcaoFiscal[];
  value: string;
  onChange: (v: string) => void;
  erro?: string | undefined;
}) {
  const id = useId();
  const [termo, setTermo] = useState("");
  const results = pesquisar(options, termo);
  const selected = options.find((o) => o.codigo === value);
  return (
    <div className="space-y-2">
      <label htmlFor={`${id}-busca`} className="block text-sm font-medium">
        Pesquisar {label}
      </label>
      <input
        id={`${id}-busca`}
        className="h-9 w-full rounded-md border border-input bg-card px-3 text-sm"
        value={termo}
        onChange={(e) => setTermo(e.target.value)}
        placeholder="Código ou descrição"
      />
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-invalid={!!erro}
        aria-describedby={`${id}-info`}
        className="h-10 w-full rounded-md border border-input bg-card px-3 text-sm"
      >
        <option value="">Selecione…</option>
        {value && !results.some((o) => o.codigo === value) && (
          <option value={value}>
            {value} — {selected?.descricao ?? "Código fora desta lista"} (selecionado)
          </option>
        )}
        {results.map((o) => (
          <option key={o.codigo} value={o.codigo}>
            {o.codigo} — {o.descricao}
          </option>
        ))}
      </select>
      <p
        id={`${id}-info`}
        className={erro ? "text-xs text-destructive" : "text-xs text-muted-foreground"}
        aria-live="polite"
      >
        {erro ||
          (selected
            ? `${selected.codigo} — ${selected.descricao}`
            : `${results.length} opções encontradas. Escolha uma opção na lista.`)}
      </p>
    </div>
  );
}

export function CatalogFields({
  value,
  onChange,
  mostrarErros,
}: {
  value?: SelecaoFiscal | undefined;
  onChange: (v: SelecaoFiscal) => void;
  mostrarErros: boolean;
}) {
  const s = value ?? fiscalVazio();
  const erros = mostrarErros ? validarCatalogo(value) : {};
  const set = (k: keyof SelecaoFiscal, v: string) =>
    onChange({
      ...s,
      catalogoId: catalogo.id,
      [k]: v,
      ...(k === "cst" && v !== s.cst ? { cClassTrib: "" } : {}),
    });
  const item = s.servico ? `${s.servico.slice(0, 2)}.${s.servico.slice(2, 4)}` : "";
  const refs = item ? catalogo.correlacoes.filter((r) => r.valores[0] === item) : [];
  return (
    <fieldset className="surface space-y-4 p-5">
      <legend className="sr-only">Códigos fiscais</legend>
      <h2 className="text-sm font-semibold">Códigos fiscais do serviço</h2>
      <p className="text-xs text-muted-foreground">
        Escolha cada código após a conferência fiscal do escritório. É possível salvar um rascunho
        incompleto. As tabelas não confirmam o enquadramento nem liberam emissão real.
      </p>
      {erros.catalogo && (
        <p role="alert" className="text-sm text-destructive">
          {erros.catalogo}
        </p>
      )}
      <div className="grid gap-5 sm:grid-cols-2">
        <Busca
          label="Serviço nacional"
          options={catalogo.servicos}
          value={s.servico}
          onChange={(v) => set("servico", v)}
          erro={erros.servico}
        />
        <Busca
          label="NBS"
          options={nbsDisponiveis}
          value={s.nbs}
          onChange={(v) => set("nbs", v)}
          erro={erros.nbs}
        />
        <Busca
          label="CST IBS/CBS"
          options={csts}
          value={s.cst}
          onChange={(v) => set("cst", v)}
          erro={erros.cst}
        />
        <Busca
          label="cClassTrib"
          options={classesNFSe.filter((c) => !s.cst || c.cst === s.cst)}
          value={s.cClassTrib}
          onChange={(v) => set("cClassTrib", v)}
          erro={erros.cClassTrib}
        />
        <Busca
          label="Indicador da operação"
          options={indopsNFSe}
          value={s.cIndOp}
          onChange={(v) => set("cIndOp", v)}
          erro={erros.cIndOp}
        />
      </div>
      <details className="rounded-md border p-3 text-xs">
        <summary className="cursor-pointer font-medium">
          Consultar correlações preliminares do Anexo VIII ({refs.length} linhas)
        </summary>
        <p className="my-3">
          Trabalho inicial em desenvolvimento. Não fundamenta regras de negócio em produção nem em
          testes. Cada linha preserva o agrupamento da planilha; confirme as alternativas com o
          responsável fiscal. Nenhum campo é preenchido automaticamente.
        </p>
        {!item && <p>Selecione um serviço nacional para consultar o item correspondente.</p>}
        {item && !refs.length && (
          <p>
            Nenhuma correlação encontrada para este item. Isso não invalida os códigos escolhidos.
          </p>
        )}
        <ul className="space-y-3">
          {refs.map((r) => (
            <li key={r.linha} className="border-t pt-2">
              Linha {r.linha}:{" "}
              {r.valores.slice(0, 10).map((v, i) =>
                v ? (
                  <span className="mr-2 inline-block" key={i}>
                    {
                      [
                        "Item LC116",
                        "Descrição",
                        "NBS",
                        "Descrição NBS",
                        "Ativ. SN",
                        "Descrição SN",
                        "indOp",
                        "Local IBS",
                        "cClassTrib",
                        "Descrição cClassTrib",
                      ][i]
                    }
                    : {v}.
                  </span>
                ) : null,
              )}
            </li>
          ))}
        </ul>
        <details className="mt-3">
          <summary>Notas da planilha sobre operações não onerosas e exterior</summary>
          {catalogo.notasCorrelacoes.map((r) => (
            <p key={r.linha}>
              Linha {r.linha}: {r.valores.join(" / ")}
            </p>
          ))}
        </details>
      </details>
      <p className="break-all text-xs text-muted-foreground">
        Referência: {catalogo.id}. Captura: {catalogo.capturadoEm}. {catalogo.vigencia}
      </p>
    </fieldset>
  );
}

export function CatalogSummary({ value }: { value?: SelecaoFiscal | undefined }) {
  return (
    <section className="surface space-y-3 p-5" aria-label="Códigos fiscais selecionados">
      <h2 className="text-sm font-semibold">Códigos fiscais selecionados</h2>
      <dl className="space-y-3">
        {fiscalLinhas(value).map((r) => (
          <div key={r.label}>
            <dt className="text-xs text-muted-foreground">{r.label}</dt>
            <dd className="text-sm">{r.texto}</dd>
          </div>
        ))}
      </dl>
      <p className="break-all text-xs">
        Catálogo selecionado: {value?.catalogoId || "Não selecionado"}. Estas escolhas precisam de
        revisão fiscal; não representam aprovação tributária.
      </p>
      <details className="text-xs">
        <summary>Fontes das tabelas disponíveis</summary>
        <ul>
          {catalogo.fontes.map((s) => (
            <li className="mt-2 break-all" key={s.arquivo}>
              {s.arquivo} — versão {s.versao || "não informada no arquivo"} — SHA256 {s.sha256}
            </li>
          ))}
        </ul>
        <p className="mt-2">{catalogo.vigencia}</p>
      </details>
    </section>
  );
}
