"""Parsing XML seguro e carga de XSD oficiais vendorizados (sem rede, sem DTD, sem entidades).

- Documentos não confiáveis: tamanho limitado, DOCTYPE/ENTITY recusados antes do parse,
  parser lxml sem rede, sem DTD e sem resolução de entidades.
- Esquemas: somente arquivos listados no MANIFEST.json do perfil, com SHA-256 conferido;
  qualquer include/import fora da allowlist do diretório do perfil é recusado.
"""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from lxml import etree

MAX_XML_BYTES = 512 * 1024  # uma DPS assinada tem poucos KB
SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"


import re

_DECL = re.compile(r"""<\?xml\s[^>]*?encoding\s*=\s*["']([^"']+)["']""")


class XmlInseguro(ValueError):
    pass


class EsquemaInvalido(RuntimeError):
    pass


def _parser() -> etree.XMLParser:
    return etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, dtd_validation=False,
                           huge_tree=False, remove_blank_text=False, collect_ids=False)


def parse_untrusted(data: bytes, max_bytes: int = MAX_XML_BYTES) -> etree._Element:
    if not isinstance(data, (bytes, bytearray)):
        raise XmlInseguro("XML deve ser bytes")
    if len(data) > max_bytes:
        raise XmlInseguro(f"XML excede o limite de {max_bytes} bytes")
    data = bytes(data)
    _prescan(data)
    return _parse_checked(data)


def _prescan(data: bytes) -> None:
    # Somente UTF-8 estrito: sem BOM UTF-16/32, sem NUL, declaração (se houver) com encoding UTF-8.
    if data[:2] in (b"\xff\xfe", b"\xfe\xff") or data[:4] in (b"\x00\x00\xfe\xff", b"\xff\xfe\x00\x00") or b"\x00" in data:
        raise XmlInseguro("Somente UTF-8 é aceito")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise XmlInseguro("Somente UTF-8 é aceito") from exc
    m = _DECL.match(text.lstrip("\ufeff"))
    if m and m.group(1) and m.group(1).lower() not in ("utf-8", "utf8"):
        raise XmlInseguro("Somente UTF-8 é aceito")
    up = text.upper()
    if "<!DOCTYPE" in up or "<!ENTITY" in up:
        raise XmlInseguro("DOCTYPE/ENTITY não permitidos")


def _parse_checked(data: bytes) -> etree._Element:
    try:
        root = etree.fromstring(data, _parser())
    except etree.XMLSyntaxError as exc:
        raise XmlInseguro("XML malformado") from exc
    # Defesa pós-parse (independente da varredura textual): nenhum DTD nem referência de entidade.
    di = root.getroottree().docinfo
    if di.doctype or di.internalDTD is not None or di.externalDTD is not None or di.system_url or di.public_id:
        raise XmlInseguro("DOCTYPE/DTD não permitidos")
    if any(isinstance(n, etree._Entity) for n in root.iter()):
        raise XmlInseguro("Referência de entidade não permitida")
    return root


def manifest() -> dict:
    return json.loads((SCHEMAS_DIR / "MANIFEST.json").read_text(encoding="utf-8"))


class _AllowlistResolver(etree.Resolver):
    def __init__(self, folder: Path, files: dict[str, str]) -> None:
        super().__init__()
        self.folder, self.files, self.loaded = folder, files, []

    def resolve(self, system_url, public_id, context):
        name = Path(str(system_url).replace("file://", "")).name
        target = (self.folder / name).resolve()
        if "://" in str(system_url) and not str(system_url).startswith("file://"):
            raise EsquemaInvalido(f"Referência externa recusada: {system_url}")
        if target.parent != self.folder or name not in self.files:
            raise EsquemaInvalido(f"Include fora da allowlist: {system_url}")
        data = target.read_bytes()
        if hashlib.sha256(data).hexdigest() != self.files[name]:
            raise EsquemaInvalido(f"Hash divergente em {name}")
        self.loaded.append(name)
        return self.resolve_string(data, context, base_url=str(target))


@lru_cache(maxsize=8)
def load_schema(profile_dir: str) -> etree.XMLSchema:
    m = manifest().get(profile_dir)
    if not m:
        raise EsquemaInvalido(f"Perfil de esquema desconhecido: {profile_dir}")
    folder = (SCHEMAS_DIR / profile_dir).resolve()
    files: dict[str, str] = m["files"]
    for name, h in files.items():
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != h:
            raise EsquemaInvalido(f"Hash divergente em {profile_dir}/{name}")
    p = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    resolver = _AllowlistResolver(folder, files)
    p.resolvers.add(resolver)
    root_path = folder / m["root"]
    doc = etree.parse(str(root_path), p)
    try:
        return etree.XMLSchema(doc)
    except etree.XMLSchemaParseError as exc:
        raise EsquemaInvalido(str(exc)) from exc


def validate(profile_dir: str, root: etree._Element) -> list[str]:
    schema = load_schema(profile_dir)
    if schema.validate(root):
        return []
    return [f"linha {e.line}: {e.message}" for e in schema.error_log]
