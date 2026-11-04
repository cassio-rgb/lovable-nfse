import { Link } from "@tanstack/react-router";
import { Building2, FlaskConical } from "lucide-react";
import { useState, type FormEvent, type ReactNode } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useEmpresa, type FonteStatus } from "./CompanyContext";
import { entrar } from "@/lib/datasource";

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
        <span className="hidden font-normal sm:inline">
          · dados fictícios, salvos apenas neste navegador
        </span>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { ds, sessao, empresa, ambiente, trocarEmpresa, encerrarSessao } = useEmpresa();
  return (
    <div className="min-h-screen">
      {ds.modo === "demo" && <DemoBanner />}
      <header className="border-b bg-card">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
          <Link to="/" className="mr-auto leading-tight">
            <span className="block text-base font-semibold text-primary">NFS-e Imóveis</span>
            <span className="block text-xs text-muted-foreground">Atual Assessoria</span>
          </Link>
          <nav
            aria-label="Principal"
            className="order-3 flex w-full gap-1 overflow-x-auto sm:order-none sm:w-auto"
          >
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
                CNPJ <span className="doc text-foreground">{empresa.cnpj}</span> ·{" "}
                {empresa.municipio}
              </span>
            )}
            <span className="ml-auto rounded-full border border-primary/30 bg-card px-2.5 py-0.5 text-xs font-medium text-primary">
              Ambiente:{" "}
              {ambiente === "producao_restrita" ? "Produção restrita (homologação)" : "Produção"}
            </span>
            <span className="text-xs text-muted-foreground">{sessao.usuario}</span>
            {ds.modo === "api" && (
              <Button variant="outline" size="sm" onClick={() => void encerrarSessao()}>
                Sair
              </Button>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        {empresa ? (
          <div key={`${ds.modo}:${sessao.usuario}:${empresa.id}`}>{children}</div>
        ) : (
          <p>Selecione uma empresa autorizada para continuar.</p>
        )}
      </main>
    </div>
  );
}

function LoginForm({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await entrar(email.trim(), password);
      onSuccess();
    } catch {
      setError(
        "Não foi possível entrar. Confira suas credenciais e a disponibilidade do serviço. Se o problema continuar, procure o responsável.",
      );
    } finally {
      setPassword("");
      setBusy(false);
    }
  }
  return (
    <form onSubmit={submit} className="mt-6 space-y-4" aria-busy={busy}>
      <div>
        <label htmlFor="login-email" className="block text-sm font-medium">
          E-mail
        </label>
        <input
          id="login-email"
          type="email"
          autoComplete="username"
          required
          disabled={busy}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mt-1 h-10 w-full rounded-md border bg-background px-3"
        />
      </div>
      <div>
        <label htmlFor="login-password" className="block text-sm font-medium">
          Senha
        </label>
        <input
          id="login-password"
          type="password"
          autoComplete="current-password"
          required
          disabled={busy}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mt-1 h-10 w-full rounded-md border bg-background px-3"
        />
      </div>
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
      <Button type="submit" disabled={busy} className="w-full">
        {busy ? "Entrando…" : "Entrar"}
      </Button>
    </form>
  );
}

export function SourceFallback({
  status,
  retry,
  demo,
}: {
  status: FonteStatus;
  retry: () => void;
  demo: () => void;
}) {
  if (status === "carregando")
    return (
      <div
        className="flex min-h-screen items-center justify-center text-sm text-muted-foreground"
        role="status"
      >
        Carregando sessão…
      </div>
    );
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="surface w-full max-w-md p-8">
        <p className="text-sm font-semibold text-primary">NFS-e Imóveis · Atual Assessoria</p>
        {status === "nao_autenticado" ? (
          <>
            <h1 className="mt-2 text-xl font-semibold">Entrar</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Entre com sua conta autorizada. Se sua sessão expirou, entre novamente para continuar.
            </p>
            <LoginForm onSuccess={retry} />
          </>
        ) : status === "acesso_negado" ? (
          <>
            <h1 className="mt-2 text-xl font-semibold">Acesso não disponível</h1>
            <p className="mt-2 text-sm text-muted-foreground" role="alert">
              Não foi possível acessar este conteúdo com sua permissão atual.
            </p>
            <Button asChild className="mt-6">
              <a href="/">Voltar ao contexto autorizado</a>
            </Button>
          </>
        ) : (
          <>
            <h1 className="mt-2 text-xl font-semibold">Serviço indisponível</h1>
            <p className="mt-2 text-sm text-muted-foreground" role="alert">
              Não foi possível carregar a sessão. Tente novamente antes de continuar.
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
