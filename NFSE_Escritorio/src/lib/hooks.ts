import { useQuery } from "@tanstack/react-query";
import { useEmpresa } from "@/components/CompanyContext";

export function useRascunhos() {
  const { ds, empresa } = useEmpresa();
  return useQuery({ queryKey: ["rascunhos", empresa!.id], queryFn: () => ds.listarRascunhos(empresa!.id) });
}

export function useEmissoes(refetch?: number) {
  const { ds, empresa } = useEmpresa();
  return useQuery({ queryKey: ["emissoes", empresa!.id], queryFn: () => ds.listarEmissoes(empresa!.id), refetchInterval: refetch ?? false });
}

export function useRascunho(id: string) {
  const { ds, empresa } = useEmpresa();
  return useQuery({ queryKey: ["rascunho", empresa!.id, id], queryFn: () => ds.obterRascunho(empresa!.id, id), retry: false });
}

export const fmtData = (iso: string) => new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
export const fmtComp = (c: string) => (c ? `${c.slice(5, 7)}/${c.slice(0, 4)}` : "—");
