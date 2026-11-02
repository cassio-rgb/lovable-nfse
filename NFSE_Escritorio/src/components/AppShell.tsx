import { Link } from "@tanstack/react-router";
import { Building2, FlaskConical } from "lucide-react";
import type { ReactNode } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useEmpresa, type FonteStatus } from "./CompanyContext";
import { API_URL, loginUrl } from "@/lib/datasource";

const NAV = [
  { to: "/", label: "Início" },
  { to: "/nova", label: "Nova NFS-e" },
  { to: "/importar", label: "Importar" },
  { to: "/historico", label: "Histórico" },
] as const;

export function DemoBanner() {
  return (
    <div role="note" className="bg-demo text-demo-foreground">
      <div className="mx-auto flex max-w-6xl items-center gap-2 px-4 py-1.5 text-sm font-semibold">
        <FlaskConical aria-hidden className="h-4 w-4" />
        Demonstração — sem emissão fiscal
        <span className="hidden font-normal sm:inline">· dados fictícios, salvos apenas neste navegador</span>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { ds, sessao, empresa, ambiente, trocarEmpresa } = useEmpresa();
  return (
    <div className="min-h-screen">
      {ds.modo === "demo" && <DemoBanner />}
      <header className="border-b bg-card">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
          <Link to="/" className="mr-auto leading-tight">
            <span className="block text-base font-semibold text-primary">NFS-e Imóveis</span>
            <span className="block text-xs text-muted-foreground">Atual Assessoria</span>
          </Link>
          <nav aria-label="Principal" className="order-3 flex w-full gap-1 overflow-x-auto sm:order-none sm:w-auto">
            {NAV.map((n) => (
              <Link
                key={n.to}
                to={n.to}
                activeOptions={{ exact: n.to === "/" }}
                className="whitespace-nowrap rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-muted hover:text-foreground data-[status=active]:bg-secondary data-[status=active]:font-medium data-[status=active]:text-secondary-foreground"
              >
                {n.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="border-t bg-muted/60">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-2 text-sm">
            <Building2 aria-hidden className="h-4 w-4 text-primary" />
            <span className="sr-only">Empresa ativa:</span>
            {sessao.empresas.length > 1 ? (
              <Select value={empresa?.id ?? ""} onValueChange={trocarEmpresa}>
                <SelectTrigger aria-label="Empresa ativa" className="h-8 w-auto min-w-64 bg-card">
                  <SelectValue placeholder="Selecione a empresa" />
                </SelectTrigger>
                <SelectContent>
                  {sessao.empresas.map((e) => (
                    <SelectItem key={e.id} value={e.id}>
                      {e.razaoSocial} · {e.cnpj}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <span className="font-medium">{empresa?.razaoSocial}</span>
            )}
            {empresa && (
              <span className="text-muted-foreground">
                CNPJ <span className="doc text-foreground">{empresa.cnpj}</span> · {empresa.municipio}
              </span>
            )}
            <span className="ml-auto rounded-full border border-primary/30 bg-card px-2.5 py-0.5 text-xs font-medium text-primary">
              Ambiente: {ambiente === "producao_restrita" ? "Produção restrita (homologação)" : "Produção"}
            </span>
            <span className="text-xs text-muted-foreground">{sessao.usuario}</span>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{empresa ? children : <p>Selecione uma empresa autorizada para continuar.</p>}</main>
    </div>
  );
}

export function SourceFallback({ status, retry, demo }: { status: FonteStatus; retry: () => void; demo: () => void }) {
  if (status === "carregando")
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground" role="status">
        Carregando…
      </div>
    );
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="surface max-w-md p-8">
        <p className="text-sm font-semibold text-primary">NFS-e Imóveis · Atual Assessoria</p>
        {status === "nao_autenticado" ? (
          <>
            <h1 className="mt-2 text-xl font-semibold">Entrar</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              O acesso é feito pelo provedor de identidade configurado no serviço fiscal. Você voltará para cá depois de entrar.
            </p>
            <Button asChild className="mt-6 w-full">
              <a href={loginUrl()}>Entrar com o provedor de identidade</a>
            </Button>
          </>
        ) : (
          <>
            <h1 className="mt-2 text-xl font-semibold">Serviço fiscal indisponível</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Não foi possível falar com o serviço fiscal em <span className="doc">{API_URL}</span>. Nenhum dado foi enviado.
            </p>
            <div className="mt-6 flex flex-col gap-2">
              <Button onClick={retry}>Tentar novamente</Button>
              <Button variant="outline" onClick={demo}>
                Abrir modo demonstração (dados fictícios, sem emissão)
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
