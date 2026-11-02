// Contratos internos do frontend. Valores monetários trafegam como string decimal
// canônica ("1234.56") e são manipulados como centavos inteiros — nunca float.

export type Ambiente = "producao_restrita" | "producao";
export type Papel = "cliente" | "escritorio";
export type TipoOperacao = "locacao" | "venda" | "arrendamento" | "administracao";

export const OPERACAO_LABEL: Record<TipoOperacao, string> = {
  locacao: "Intermediação/administração de locação",
  venda: "Intermediação de venda de imóvel",
  arrendamento: "Arrendamento",
  administracao: "Administração de imóveis",
};

export interface Empresa {
  id: string;
  razaoSocial: string;
  cnpj: string; // textual, nunca número
  municipio: string;
  ficticia?: boolean | undefined;
}

export interface Liberacao {
  empresaId: string;
  operacao: TipoOperacao;
  ambiente: Ambiente;
  versao: number;
  evidencia: string;
}

export type EstadoFiscal =
  | "rascunho"
  | "com_pendencias"
  | "revisado"
  | "na_fila"
  | "transmitindo"
  | "resultado_desconhecido"
  | "emitida"
  | "rejeitada"
  | "erro_pre_envio";

export const ESTADO_LABEL: Record<EstadoFiscal, string> = {
  rascunho: "Rascunho — não emitido",
  com_pendencias: "Com pendências — não emitido",
  revisado: "Revisado — não emitido",
  na_fila: "Na fila de transmissão",
  transmitindo: "Transmitindo",
  resultado_desconhecido: "Resultado desconhecido",
  emitida: "Emitida",
  rejeitada: "Rejeitada",
  erro_pre_envio: "Erro técnico antes do envio — não emitido",
};

export interface Tomador {
  documento: string; // CPF/CNPJ textual
  nome: string;
  email?: string | undefined;
}

export interface SelecaoFiscal {
  catalogoId: string;
  servico: string;
  nbs: string;
  cst: string;
  cClassTrib: string;
  cIndOp: string;
}

export interface DadosRascunho {
  fiscal?: SelecaoFiscal | undefined;
  tomador: Tomador;
  operacao: TipoOperacao | "";
  competencia: string; // AAAA-MM
  valor: string; // decimal canônico "1234.56" ou ""
  descricao: string;
  imovel: string;
}

export interface Origem {
  tipo: "manual" | "importacao";
  sistema?: string | undefined;
  idOrigem?: string | undefined;
  loteId?: string | undefined;
  linha?: number | undefined;
}

export interface Rascunho {
  id: string;
  empresaId: string;
  versao: number;
  dados: DadosRascunho;
  origem: Origem;
  criadoEm: string;
  atualizadoEm: string;
  revisao?: Revisao | undefined;
  emissaoId?: string | undefined;
}

export interface Revisao {
  id: string;
  rascunhoId: string;
  versao: number;
  hash: string;
  em: string;
  /** Calculado pelo serviço fiscal (autoridade); ausente no modo demonstração. */
  valida?: boolean | undefined;
}

export type Cenario = "aceita" | "rejeitada" | "desconhecido";

export interface Emissao {
  id: string;
  empresaId: string;
  rascunhoId: string;
  versao: number;
  ambiente: Ambiente;
  identidadeDps: string;
  snapshot: DadosRascunho;
  estado: EstadoFiscal;
  simulacao: boolean;
  cenario?: Cenario | undefined;
  criadoEm: string;
  atualizadoEm: string;
  retorno?: {
    chave?: string | undefined;
    numero?: string | undefined;
    codigo?: string | undefined;
    mensagem?: string | undefined;
    detalheTecnico?: string | undefined;
  };
}
