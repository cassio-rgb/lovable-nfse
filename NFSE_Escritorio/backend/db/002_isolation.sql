-- Papéis e isolamento. A API conecta com um login membro de nfse_api (não dono das tabelas,
-- não superusuário) e define app.user_id por transação; o worker usa nfse_worker.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nfse_api') THEN CREATE ROLE nfse_api NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nfse_worker') THEN CREATE ROLE nfse_worker NOLOGIN; END IF;
END $$;

DO $$ DECLARE t text; BEGIN
  FOREACH t IN ARRAY ARRAY['draft','import_batch','import_row','review','emission','attempt','job','document'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format($p$CREATE POLICY %I_member ON %I TO nfse_api USING (EXISTS (
      SELECT 1 FROM membership m WHERE m.company_id = %I.company_id
        AND m.user_id = current_setting('app.user_id', true) AND m.revoked_at IS NULL))$p$, t, t, t);
    EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON %I TO nfse_api', t);
  END LOOP;
  FOREACH t IN ARRAY ARRAY['emission','attempt','job','document'] LOOP
    EXECUTE format('CREATE POLICY %I_worker ON %I TO nfse_worker USING (true)', t, t);
  END LOOP;
END $$;

GRANT SELECT ON company, membership, operation_release TO nfse_api;
GRANT SELECT, INSERT, UPDATE ON dps_sequence TO nfse_api;
GRANT INSERT ON technical_event TO nfse_api, nfse_worker;
GRANT SELECT, UPDATE ON emission, job TO nfse_worker;
GRANT INSERT ON attempt, document TO nfse_worker;
GRANT SELECT ON attempt, document TO nfse_worker;

-- Snapshot enviado e identidade DPS são imutáveis.
CREATE FUNCTION forbid_snapshot_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.snapshot IS DISTINCT FROM OLD.snapshot OR NEW.dps_identity IS DISTINCT FROM OLD.dps_identity
     OR NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key OR NEW.fingerprint IS DISTINCT FROM OLD.fingerprint THEN
    RAISE EXCEPTION 'snapshot/identidade DPS imutáveis';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER emission_immutable BEFORE UPDATE ON emission FOR EACH ROW EXECUTE FUNCTION forbid_snapshot_change();

GRANT USAGE ON SCHEMA public TO nfse_api, nfse_worker;
