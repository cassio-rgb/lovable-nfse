"""Storage privado com vínculo por empresa e integridade SHA-256."""
from __future__ import annotations

import hashlib
import re
import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from .auth import AcessoNegado
from .ports import Storage

_SEGMENT = re.compile(r"^[A-Za-z0-9._-]+$")


def _segmento(valor: str, nome: str) -> str:
    if not valor or not _SEGMENT.fullmatch(valor) or valor in {".", ".."}:
        raise ValueError(f"{nome} inválido")
    return valor


class MemoryStorage:
    durable = False  # somente teste/demonstração

    def __init__(self) -> None:
        self._o: dict[str, tuple[str, bytes, str]] = {}

    def put(self, empresa_id: str, kind: str, data: bytes) -> tuple[str, str]:
        ref = f"{empresa_id}/{kind}/{uuid.uuid4().hex}"
        h = hashlib.sha256(data).hexdigest()
        self._o[ref] = (empresa_id, data, h)
        return ref, h

    def get(self, empresa_id: str, ref: str) -> bytes:
        o = self._o.get(ref)
        if not o or o[0] != empresa_id:
            raise AcessoNegado()
        if hashlib.sha256(o[1]).hexdigest() != o[2]:
            raise RuntimeError("Integridade do artefato violada")
        return o[1]


class SupabaseS3Storage(Storage):
    """Storage durável no endpoint S3 compatível do Supabase.

    As credenciais são exclusivas do backend/worker. Referências incluem a empresa
    no primeiro segmento; o adaptador nunca gera URL pública nem aceita referência
    de outra empresa.
    """

    durable = True

    def __init__(
        self,
        endpoint: str,
        region: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
        client=None,
    ) -> None:
        if not endpoint.startswith("https://"):
            raise ValueError("Endpoint S3 deve usar HTTPS")
        if not all((region, access_key_id, secret_access_key, bucket)):
            raise ValueError("Configuração S3 incompleta")
        self.bucket = bucket
        self._client = client or boto3.client(
            "s3",
            endpoint_url=endpoint.rstrip("/"),
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def put(self, empresa_id: str, kind: str, data: bytes) -> tuple[str, str]:
        empresa = _segmento(empresa_id, "empresa_id")
        tipo = _segmento(kind, "kind")
        ref = f"{empresa}/{tipo}/{uuid.uuid4().hex}"
        sha = hashlib.sha256(data).hexdigest()
        self._client.put_object(
            Bucket=self.bucket,
            Key=ref,
            Body=data,
            ContentType="application/octet-stream",
            Metadata={"sha256": sha, "company-id": empresa},
        )
        return ref, sha

    def get(self, empresa_id: str, ref: str) -> bytes:
        empresa = _segmento(empresa_id, "empresa_id")
        prefixo = f"{empresa}/"
        if not ref.startswith(prefixo) or ".." in ref.split("/"):
            raise AcessoNegado()
        try:
            obj = self._client.get_object(Bucket=self.bucket, Key=ref)
        except ClientError as exc:
            status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status in {403, 404}:
                raise AcessoNegado() from exc
            raise

        meta = {str(k).lower(): str(v) for k, v in (obj.get("Metadata") or {}).items()}
        if meta.get("company-id") and meta["company-id"] != empresa:
            raise AcessoNegado()
        body = obj["Body"].read()
        esperado = meta.get("sha256")
        if not esperado or hashlib.sha256(body).hexdigest() != esperado:
            raise RuntimeError("Integridade do artefato violada")
        return body
