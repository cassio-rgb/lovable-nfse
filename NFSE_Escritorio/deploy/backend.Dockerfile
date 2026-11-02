# Imagem do serviço fiscal (API e worker do mesmo código). Hospedagem a confirmar.
FROM python:3.12-slim
WORKDIR /srv
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir .
COPY backend/ ./
COPY shared/catalogos-fiscais.json ./shared/catalogos-fiscais.json
USER 10001
# API:    uvicorn app.main:app (recusa iniciar até haver infraestrutura durável) --host 0.0.0.0 --port 8000
# Worker: python -m app.worker_main (a criar junto com PostgresRepository)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
