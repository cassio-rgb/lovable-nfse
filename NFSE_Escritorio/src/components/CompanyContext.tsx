import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import type { Ambiente, Empresa } from "@/lib/contracts";
import {
  API_URL,
  createApiSource,
  createDemoSource,
  NaoAutenticado,
  sair,
  type DataSource,
  type Sessao,
} from "@/lib/datasource";

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
  encerrarSessao: () => Promise<void>;
}

const C = createContext<Ctx | null>(null);
export const useEmpresa = () => {
  const c = useContext(C);
  if (!c) throw new Error("CompanyProvider ausente");
  return c;
};

const EMP_KEY = "nfse-imoveis:empresa-ativa";

export type FonteStatus =
  "carregando" | "nao_autenticado" | "acesso_negado" | "indisponivel" | "pronto";

export function CompanyProvider({
  children,
  fallback,
}: {
  children: ReactNode;
  fallback: (s: FonteStatus, retry: () => void, demo: () => void) => ReactNode;
}) {
  const [forcarDemo, setForcarDemo] = useState(false);
  const [acesso, setAcesso] = useState<FonteStatus | null>(null);
  const [encerrando, setEncerrando] = useState(false);
  const [erroSaida, setErroSaida] = useState(false);
  const qc = useQueryClient();
  const [sessaoPronta, setSessaoPronta] = useState<Sessao | null>(null);
  const limpar = useCallback(() => {
    setSessaoPronta(null);
    void qc.cancelQueries();
    qc.clear();
  }, [qc]);
  const negar = useCallback(
    (status: number) => {
      setAcesso(status === 401 ? "nao_autenticado" : "acesso_negado");
      limpar();
    },
    [limpar],
  );
  const ds = useMemo(
    () => (API_URL && !forcarDemo ? createApiSource(API_URL, negar) : createDemoSource()),
    [forcarDemo, negar],
  );
  const q = useQuery({
    queryKey: ["sessao", ds.modo],
    queryFn: () => ds.sessao(),
    retry: false,
    enabled: !acesso && !encerrando,
    refetchInterval: ds.modo === "api" ? 60000 : false,
  });
  const [empresaId, setEmpresaId] = useState<string | null>(null);
  const [pendente, setPendente] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);
  const [erroSalvar, setErroSalvar] = useState<string | null>(null);
  const guard = useRef<Guard | null>(null);
  const anterior = useRef("");

  useEffect(() => {
    if (!q.data) return;
    const identidade = `${ds.modo}:${q.data.usuario}:${q.data.empresas.map((e) => e.id).join(",")}`;
    if (anterior.current !== identidade) {
      void qc.cancelQueries({ predicate: (x) => x.queryKey[0] !== "sessao" });
      qc.removeQueries({ predicate: (x) => x.queryKey[0] !== "sessao" });
      guard.current = null;
      setPendente(null);
      anterior.current = identidade;
    }
    const key = `${EMP_KEY}:${ds.modo}:${q.data.usuario}`;
    const saved = window.localStorage.getItem(key);
    setEmpresaId(
      (atual) =>
        q.data.empresas.find((e) => e.id === atual)?.id ??
        q.data.empresas.find((e) => e.id === saved)?.id ??
        q.data.empresas[0]?.id ??
        null,
    );
    setSessaoPronta(q.data);
  }, [q.data, ds.modo, qc]);

  const aplicar = useCallback(
    (id: string) => {
      if (!q.data?.empresas.some((e) => e.id === id)) return;
      setEmpresaId(id);
      window.localStorage.setItem(`${EMP_KEY}:${ds.modo}:${q.data.usuario}`, id);
      void qc.cancelQueries({ predicate: (x) => x.queryKey[0] !== "sessao" });
      qc.removeQueries({ predicate: (x) => x.queryKey[0] !== "sessao" });
    },
    [qc, q.data, ds.modo],
  );

  const trocarEmpresa = useCallback(
    (id: string) => {
      if (id === empresaId || !q.data?.empresas.some((e) => e.id === id)) return;
      if (guard.current?.dirty) {
        setErroSalvar(null);
        setPendente(id);
      } else aplicar(id);
    },
    [empresaId, aplicar, q.data],
  );

  const encerrarSessao = useCallback(async () => {
    setEncerrando(true);
    setErroSaida(false);
    limpar();
    guard.current = null;
    setEmpresaId(null);
    setPendente(null);
    try {
      await sair();
      setAcesso("nao_autenticado");
      setEncerrando(false);
    } catch {
      // A sessão remota pode continuar válida. Não exibir dados nem confirmar saída.
      setErroSaida(true);
    }
  }, [limpar]);

  const usarDemonstracao = useCallback(() => {
    limpar();
    setEmpresaId(null);
    guard.current = null;
    setAcesso(null);
    setForcarDemo(true);
  }, [limpar]);

  const value = useMemo<Ctx | null>(() => {
    if (!q.data || sessaoPronta !== q.data || acesso || encerrando || q.isError) return null;
    return {
      ds,
      sessao: q.data,
      empresa: q.data.empresas.find((e) => e.id === empresaId),
      ambiente: "producao_restrita",
      trocarEmpresa,
      registrarGuarda: (g) => (guard.current = g),
      usarDemonstracao,
      encerrarSessao,
    };
  }, [
    q.data,
    sessaoPronta,
    q.isError,
    acesso,
    encerrando,
    ds,
    empresaId,
    trocarEmpresa,
    usarDemonstracao,
    encerrarSessao,
  ]);

  if (encerrando)
    return (
      <div className="mx-auto max-w-md p-8" role={erroSaida ? "alert" : "status"}>
        <p>
          {erroSaida
            ? "Não foi possível encerrar a sessão. Tente novamente para confirmar a saída."
            : "Encerrando sessão…"}
        </p>
        {erroSaida && <Button onClick={() => void encerrarSessao()}>Tentar sair novamente</Button>}
      </div>
    );

  if (!value) {
    const status: FonteStatus =
      acesso ??
      (q.isLoading || q.isFetching || (q.data && sessaoPronta !== q.data)
        ? "carregando"
        : q.error instanceof NaoAutenticado
          ? "nao_autenticado"
          : "indisponivel");
    return (
      <>
        {fallback(
          status,
          () => {
            limpar();
            setEmpresaId(null);
            setAcesso(null);
            void q.refetch();
          },
          usarDemonstracao,
        )}
      </>
    );
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
              Você está editando um rascunho de <strong>{value.empresa?.razaoSocial}</strong>. Antes
              de trocar para <strong>{destino?.razaoSocial}</strong>, escolha o que fazer com as
              alterações.
            </AlertDialogDescription>
          </AlertDialogHeader>
          {erroSalvar && (
            <p
              role="alert"
              className="rounded-md bg-danger-soft px-3 py-2 text-sm text-destructive"
            >
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
