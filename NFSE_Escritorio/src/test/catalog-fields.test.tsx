import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useState } from "react";
import { CatalogFields, CatalogSummary } from "@/components/CatalogFields";
import { catalogo } from "@/lib/catalogos";
import type { SelecaoFiscal } from "@/lib/contracts";

const filled = (): SelecaoFiscal => ({
  catalogoId: catalogo.id,
  servico: "010101",
  nbs: "1.0101.11.00",
  cst: "000",
  cClassTrib: "000001",
  cIndOp: "010101",
});
afterEach(cleanup);
function Form() {
  const [v, set] = useState<SelecaoFiscal | undefined>();
  return (
    <>
      <CatalogFields value={v} onChange={set} mostrarErros={false} />
      <CatalogSummary value={v} />
    </>
  );
}
describe("consulta acessível de códigos", () => {
  it("pesquisar não escolhe código, seleção é explícita e troca CST limpa classe", () => {
    render(<Form />);
    const service = screen.getByRole("combobox", { name: "Serviço nacional" });
    fireEvent.change(screen.getByLabelText("Pesquisar Serviço nacional"), {
      target: { value: "010101" },
    });
    expect(service).toHaveValue("");
    fireEvent.change(service, { target: { value: "010101" } });
    expect(service).toHaveValue("010101");
    fireEvent.change(screen.getByRole("combobox", { name: "CST IBS/CBS" }), {
      target: { value: "000" },
    });
    fireEvent.change(screen.getByRole("combobox", { name: "cClassTrib" }), {
      target: { value: "000001" },
    });
    expect(screen.getByRole("combobox", { name: "cClassTrib" })).toHaveValue("000001");
    fireEvent.change(screen.getByRole("combobox", { name: "CST IBS/CBS" }), {
      target: { value: "200" },
    });
    expect(screen.getByRole("combobox", { name: "cClassTrib" })).toHaveValue("");
  });
  it("revisão apresenta códigos, descrições e fonte", () => {
    render(<CatalogSummary value={filled()} />);
    for (const code of ["010101", "1.0101.11.00", "000", "000001"])
      expect(screen.getAllByText(new RegExp(code)).length).toBeGreaterThan(0);
    expect(screen.getByText(/Catálogo selecionado/)).toHaveTextContent(catalogo.id);
    expect(screen.getByText(/não representam aprovação tributária/)).toBeInTheDocument();
  });
});
