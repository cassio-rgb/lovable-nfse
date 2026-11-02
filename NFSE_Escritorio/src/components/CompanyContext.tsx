import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import type { Ambiente, Empresa } from "@/lib/contracts";
import { API_URL, createApiSource, createDemoSource, NaoAutenticado, type DataSource, type Sessao } from "@/lib/datasource";

interface Guard {
  dirty: boolean;
  save: () => Promise<boolean>;
  discard: () => void;
}

interface Ctx {
  ds: DataSource;
  sessao: Sessao;
  empresa: Empresa | undefined;
  ambiente: Ambiente;
  trocarEmpresa: (id: string) => void;
  registrarGuarda: (g: Guard | null) => void;
  usarDemonstracao: () => void;
}

const C = createContext<Ctx | null>(null);
export const useEmpresa = () => {
  const c = useContext(C);
  if (!c) throw new Error("CompanyProvider ausente");
  return c;
};

const EMP_KEY = "nfse-imoveis:empresa-ativa";

export type FonteStatus = "carregando" | "nao_autenticado" | "indisponivel" | "pronto";

export function CompanyProvider({ children, fallback }: { children: ReactNode; fallback: (s: FonteStatus, retry: () => void, demo: () => void) => ReactNode }) {
  const [forcarDemo, setForcarDemo] = useState(false);
  const ds = useMemo(() => (API_URL && !forcarDemo ? createApiSource(API_URL) : createDemoSource()), [forcarDemo]);
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["sessao", ds.modo], queryFn: () => ds.sessao(), retry: false });
  const [empresaId, setEmpresaId] = useState<string | null>(null);
  const [pendente, setPendente] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);
  const [erroSalvar, setErroSalvar] = useState<string | null>(null);
  const guard = useRef<Guard | null>(null);

  useEffect(() => {
    if (!q.data) return;
    const saved = window.localStorage.getItem(EMP_KEY);
    const ok = q.data.empresas.find((e) => e.id === saved) ?? (q.data.empresas.length === 1 ? q.data.empresas[0] : q.data.empresas[0]);
    setEmpresaId(ok?.id ?? null);
  }, [q.data]);

  const aplicar = useCallback(
    (id: string) => {
      setEmpresaId(id);
      window.localStorage.setItem(EMP_KEY, id);
      // Limpa caches de outro contexto de empresa.
      qc.removeQueries({ predicate: (x) => x.queryKey[0] !== "sessao" });
    },
    [qc],
  );

  const trocarEmpresa = useCallback(
    (id: string) => {
      if (id === empresaId) return;
      if (guard.current?.dirty) {
        setErroSalvar(null);
        setPendente(id);
      } else aplicar(id);
    },
    [empresaId, aplicar],
  );

  const value = useMemo<Ctx | null>(() => {
    if (!q.data) return null;
    return {
      ds,
      sessao: q.data,
      empresa: q.data.empresas.find((e) => e.id === empresaId),
      ambiente: "producao_restrita",
      trocarEmpresa,
      registrarGuarda: (g) => (guard.current = g),
      usarDemonstracao: () => setForcarDemo(true),
    };
  }, [q.data, ds, empresaId, trocarEmpresa]);

  if (!value) {
    const status: FonteStatus = q.isLoading ? "carregando" : q.error instanceof NaoAutenticado ? "nao_autenticado" : "indisponivel";
    return <>{fallback(status, () => q.refetch(), () => setForcarDemo(true))}</>;
  }

  const destino = q.data!.empresas.find((e) => e.id === pendente);

  return (
    <C.Provider value={value}>
      {children}
      <AlertDialog open={!!pendente} onOpenChange={(o) => !o && !salvando && setPendente(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Há alterações não salvas</AlertDialogTitle>
            <AlertDialogDescription>
              Você está editando um rascunho de <strong>{value.empresa?.razaoSocial}</strong>. Antes de trocar para{" "}
              <strong>{destino?.razaoSocial}</strong>, escolha o que fazer com as alterações.
            </AlertDialogDescription>
          </AlertDialogHeader>
          {erroSalvar && (
            <p role="alert" className="rounded-md bg-danger-soft px-3 py-2 text-sm text-destructive">
              {erroSalvar} A empresa não foi trocada e seus dados continuam no formulário.
            </p>
          )}
          <AlertDialogFooter className="flex-wrap gap-2 sm:gap-2">
            <Button variant="ghost" disabled={salvando} onClick={() => setPendente(null)}>
              Permanecer
            </Button>
            <Button
              variant="outline"
              disabled={salvando}
              onClick={() => {
                guard.current?.discard();
                guard.current = null;
                const id = pendente!;
                setPendente(null);
                aplicar(id);
              }}
            >
              Descartar alterações e trocar
            </Button>
            <Button
              disabled={salvando}
              onClick={async () => {
                setSalvando(true);
                setErroSalvar(null);
                const ok = await guard.current!.save().catch(() => false);
                setSalvando(false);
                if (!ok) {
                  setErroSalvar("Não foi possível salvar o rascunho.");
                  return;
                }
                guard.current = null;
                const id = pendente!;
                setPendente(null);
                aplicar(id);
              }}
            >
              {salvando ? "Salvando…" : "Salvar e trocar"}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </C.Provider>
  );
}
