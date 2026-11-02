import { AlertTriangle, CheckCircle2, CircleDashed, FileClock, HelpCircle, Loader2, XCircle } from "lucide-react";
import type { EstadoFiscal } from "@/lib/contracts";
import { ESTADO_LABEL } from "@/lib/contracts";
import { cn } from "@/lib/utils";

const STYLE: Record<EstadoFiscal, { cls: string; Icon: typeof CheckCircle2 }> = {
  rascunho: { cls: "bg-muted text-muted-foreground border-border", Icon: CircleDashed },
  com_pendencias: { cls: "bg-warning-soft text-warning-foreground border-warning/40", Icon: AlertTriangle },
  revisado: { cls: "bg-info-soft text-accent-foreground border-primary/30", Icon: FileClock },
  na_fila: { cls: "bg-info-soft text-accent-foreground border-primary/30", Icon: Loader2 },
  transmitindo: { cls: "bg-info-soft text-accent-foreground border-primary/30", Icon: Loader2 },
  resultado_desconhecido: { cls: "bg-warning-soft text-warning-foreground border-warning/50", Icon: HelpCircle },
  emitida: { cls: "bg-success-soft text-success border-success/40", Icon: CheckCircle2 },
  rejeitada: { cls: "bg-danger-soft text-destructive border-destructive/40", Icon: XCircle },
  erro_pre_envio: { cls: "bg-danger-soft text-destructive border-destructive/40", Icon: AlertTriangle },
};

export function StatusBadge({ estado, simulacao, className }: { estado: EstadoFiscal; simulacao?: boolean | undefined; className?: string }) {
  const { cls, Icon } = STYLE[estado];
  const spin = estado === "na_fila" || estado === "transmitindo";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium", cls, className)}>
      <Icon aria-hidden className={cn("h-3.5 w-3.5", spin && "animate-spin")} />
      {simulacao && estado === "emitida" ? "Simulação: aceita — não emitida" : simulacao && estado === "rejeitada" ? "Simulação: rejeitada" : ESTADO_LABEL[estado]}
    </span>
  );
}

export function Notice({ tone = "info", title, children }: { tone?: "info" | "warning" | "danger" | "success" | undefined; title: string; children?: React.ReactNode }) {
  const cls = {
    info: "bg-info-soft border-primary/25",
    warning: "bg-warning-soft border-warning/40",
    danger: "bg-danger-soft border-destructive/30",
    success: "bg-success-soft border-success/30",
  }[tone];
  return (
    <div role={tone === "danger" ? "alert" : "status"} className={cn("rounded-md border px-4 py-3 text-sm", cls)}>
      <p className="font-semibold">{title}</p>
      {children && <div className="mt-1 text-foreground/80">{children}</div>}
    </div>
  );
}
