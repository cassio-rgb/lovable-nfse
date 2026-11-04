import { Link } from "@tanstack/react-router";
import { ShieldOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useEffect, useRef } from "react";

/** Mensagem genérica: não confirma nem nega a existência do recurso (M05). */
export function AccessDenied() {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { heading.current?.focus(); }, []);
  return (
    <div className="surface mx-auto max-w-lg p-8 text-center">
      <ShieldOff aria-hidden className="mx-auto h-8 w-8 text-muted-foreground" />
      <h1 ref={heading} data-page-focus tabIndex={-1} className="mt-3 text-xl font-semibold">Conteúdo indisponível</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Este conteúdo não está disponível para a empresa ativa ou para o seu acesso. Volte ao início para continuar com uma empresa autorizada.
      </p>
      <Button asChild className="mt-6">
        <Link to="/">Voltar ao início</Link>
      </Button>
    </div>
  );
}
