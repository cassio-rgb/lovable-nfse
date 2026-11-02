-- NFS-e Imóveis — esquema normalizado (PostgreSQL >= 14).
-- Ids: uuid em todas as entidades; timestamps: timestamptz (UTC).
-- Relacionamentos usam (company_id, id) para que referências não cruzem empresas.
CREATE TABLE company (
  id uuid PRIMARY KEY,
  cnpj text NOT NULL UNIQUE CHECK (cnpj ~ '^\d{14}$'),
  razao_social text NOT NULL,
  municipio text NOT NULL,
  municipio_ibge text
);

CREATE TABLE membership (
  user_id text NOT NULL,
  company_id uuid NOT NULL REFERENCES company(id),
  permissions text[] NOT NULL,
  revoked_at timestamptz,
  PRIMARY KEY (user_id, company_id)
);

CREATE TABLE operation_release (
  company_id uuid NOT NULL REFERENCES company(id),
  operacao text NOT NULL CHECK (operacao IN ('locacao','venda','arrendamento','administracao')),
  ambiente text NOT NULL CHECK (ambiente IN ('producao_restrita','producao')),
  versao int NOT NULL,
  valid_from timestamptz NOT NULL DEFAULT now(),
  valid_to timestamptz,
  evidencia text NOT NULL CHECK (length(evidencia) > 0),
  autor text NOT NULL,
  PRIMARY KEY (company_id, operacao, ambiente, versao)
);

CREATE TABLE draft (
  company_id uuid NOT NULL REFERENCES company(id),
  id uuid NOT NULL,
  versao int NOT NULL DEFAULT 1 CHECK (versao >= 1),
  dados jsonb NOT NULL,
  origem jsonb NOT NULL,
  emission_id uuid,
  criado_em timestamptz NOT NULL DEFAULT now(),
  atualizado_em timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (company_id, id)
);

CREATE TABLE import_batch (
  company_id uuid NOT NULL REFERENCES company(id),
  id uuid NOT NULL,
  layout text NOT NULL,
  totals jsonb NOT NULL,
  original_ref text,            -- storage privado ainda não conectado
  criado_em timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (company_id, id)
);

CREATE TABLE import_row (
  company_id uuid NOT NULL,
  batch_id uuid NOT NULL,
  linha int NOT NULL,
  sistema_origem text NOT NULL,
  id_origem text NOT NULL,
  conteudo text NOT NULL,       -- forma canônica, para detectar conflito
  draft_id uuid NOT NULL,
  FOREIGN KEY (company_id, batch_id) REFERENCES import_batch(company_id, id),
  FOREIGN KEY (company_id, draft_id) REFERENCES draft(company_id, id) ON DELETE CASCADE,
  UNIQUE (company_id, sistema_origem, id_origem)
);

CREATE TABLE review (
  company_id uuid NOT NULL,
  id uuid NOT NULL,
  draft_id uuid NOT NULL,
  versao int NOT NULL,
  hash text NOT NULL,
  user_id text NOT NULL,
  em timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (company_id, id),
  FOREIGN KEY (company_id, draft_id) REFERENCES draft(company_id, id) ON DELETE CASCADE
);

CREATE TABLE emission (
  company_id uuid NOT NULL,
  id uuid NOT NULL,
  draft_id uuid NOT NULL,
  versao int NOT NULL,
  ambiente text NOT NULL CHECK (ambiente IN ('producao_restrita','producao')),
  dps_identity text NOT NULL,
  snapshot jsonb NOT NULL,
  review_id uuid NOT NULL,
  idempotency_key text NOT NULL,
  fingerprint text NOT NULL,
  estado text NOT NULL CHECK (estado IN ('na_fila','transmitindo','resultado_desconhecido','emitida','rejeitada','erro_pre_envio')),
  tentativas int NOT NULL DEFAULT 0,
  resultado jsonb,
  documento_ref text,
  criado_em timestamptz NOT NULL DEFAULT now(),
  atualizado_em timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (company_id, id),
  UNIQUE (company_id, ambiente, dps_identity),
  UNIQUE (company_id, idempotency_key),
  UNIQUE (company_id, draft_id, versao, ambiente),
  FOREIGN KEY (company_id, review_id) REFERENCES review(company_id, id),
  FOREIGN KEY (company_id, draft_id) REFERENCES draft(company_id, id)
);

ALTER TABLE draft ADD CONSTRAINT draft_emission_fk
  FOREIGN KEY (company_id, emission_id) REFERENCES emission(company_id, id) DEFERRABLE INITIALLY DEFERRED;

-- Reserva de numeração: UPSERT atômico; valor consumido nunca é reaproveitado.
CREATE TABLE dps_sequence (
  company_id uuid NOT NULL REFERENCES company(id),
  ambiente text NOT NULL,
  last_value bigint NOT NULL,
  PRIMARY KEY (company_id, ambiente)
);

CREATE TABLE attempt (
  company_id uuid NOT NULL,
  emission_id uuid NOT NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  fence bigint NOT NULL,
  outcome text,
  FOREIGN KEY (company_id, emission_id) REFERENCES emission(company_id, id)
);

-- Um job por emissão; `fence` aumenta a cada claim (fencing token).
CREATE TABLE job (
  company_id uuid NOT NULL,
  emission_id uuid NOT NULL,
  tipo text NOT NULL CHECK (tipo IN ('transmitir','consultar')),
  situacao text NOT NULL CHECK (situacao IN ('pendente','em_execucao','concluido')),
  fence bigint NOT NULL DEFAULT 0,
  owner text,
  lease_until timestamptz,
  run_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (company_id, emission_id),
  FOREIGN KEY (company_id, emission_id) REFERENCES emission(company_id, id)
);
CREATE INDEX job_ready ON job (situacao, run_at);

CREATE TABLE document (
  company_id uuid NOT NULL,
  id uuid NOT NULL,
  emission_id uuid,
  ref text NOT NULL,
  sha256 text NOT NULL,
  tipo text NOT NULL,
  PRIMARY KEY (company_id, id),
  FOREIGN KEY (company_id, emission_id) REFERENCES emission(company_id, id)
);

CREATE TABLE technical_event (
  ts timestamptz NOT NULL DEFAULT now(),
  correlation_id text NOT NULL,
  categoria text NOT NULL,
  codigo text,
  duracao_ms int
);
