"""Catálogo del lote: qué se ingirió, qué se apartó y por qué.

En simple: el inventario de un lote guardado en un archivo de texto legible. Se
escribe de forma que no pueda quedar a medias —primero en un archivo temporal y
luego se sustituye de un golpe—, así que un corte de luz nunca deja el catálogo
corrupto: o está el anterior entero, o el nuevo entero.

Guarda las rutas **relativas** a la carpeta del lote, de modo que mover la
carpeta no lo invalida y el archivo no lleva dentro el nombre de nadie. Y lleva
un número de versión, porque las etapas siguientes le añadirán secciones y un
catálogo escrito hoy tiene que seguir leyéndose mañana.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from media_optimizer.core import InvalidInputError, MediaType, Orientation
from media_optimizer.ingest import filesystem
from media_optimizer.ingest.quarantine import QuarantinedAsset, QuarantineReason, TriageResult

CATALOG_VERSION = 1
CATALOG_FILENAME = "catalog.json"

_TEMPORAL_SUFIJO = ".tmp"
_INDENTACION = 2


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """Un asset aceptado, tal como queda registrado en el catálogo."""

    content_hash: str
    source: str
    media_type: MediaType
    width: int
    height: int

    @property
    def orientation(self) -> Orientation:
        """Orientación derivada de las medidas guardadas."""
        if self.height > self.width:
            return Orientation.VERTICAL
        if self.width > self.height:
            return Orientation.HORIZONTAL
        return Orientation.SQUARE


@dataclass(frozen=True, slots=True)
class QuarantineRecord:
    """Un asset apartado, con la causa que lo dejó fuera."""

    source: str
    reason: QuarantineReason
    detail: str


@dataclass(frozen=True, slots=True)
class Catalog:
    """Inventario completo de un lote.

    Las dos listas se ordenan por ruta al construirse: el orden es un dato del
    catálogo, no el resultado accidental de en qué orden llegaron los archivos.
    Así dos catálogos con el mismo contenido son iguales y producen el mismo
    archivo, sin importar cómo se armaron.
    """

    root: Path
    entries: tuple[CatalogEntry, ...] = ()
    quarantined: tuple[QuarantineRecord, ...] = ()
    version: int = field(default=CATALOG_VERSION)

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(sorted(self.entries, key=lambda e: e.source)))
        object.__setattr__(
            self, "quarantined", tuple(sorted(self.quarantined, key=lambda r: r.source))
        )


def save_catalog(catalog: Catalog, directory: Path) -> Path:
    """Guarda el catálogo de forma que nunca quede a medias.

    Escribe primero un archivo temporal en la misma carpeta y luego lo sustituye
    en un solo paso: si algo falla antes, el catálogo anterior sigue intacto.
    """
    destino = directory / CATALOG_FILENAME
    temporal = directory / (CATALOG_FILENAME + _TEMPORAL_SUFIJO)
    texto = json.dumps(
        _a_diccionario(catalog), indent=_INDENTACION, sort_keys=True, ensure_ascii=False
    )
    filesystem.write_bytes(temporal, (texto + "\n").encode("utf-8"))
    filesystem.replace_atomic(temporal, destino)
    return destino


def load_catalog(directory: Path) -> Catalog:
    """Lee el catálogo de una carpeta, validándolo como entrada no confiable.

    Raises:
        InvalidInputError: si falta, no es JSON válido, trae una versión
            desconocida o le falta algún campo obligatorio.
    """
    origen = directory / CATALOG_FILENAME
    if not filesystem.exists(origen):
        msg = f"no hay catálogo en la carpeta: {directory}"
        raise InvalidInputError(msg)
    try:
        datos = json.loads(filesystem.read_bytes(origen).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        msg = f"el catálogo no es un JSON válido ({origen}): {error}"
        raise InvalidInputError(msg) from error
    return _desde_diccionario(datos, origen)


def catalog_from_triage(
    root: Path,
    triage: TriageResult,
    sizes: dict[Path, tuple[int, int]],
    hashes: dict[Path, str],
) -> Catalog:
    """Arma un catálogo a partir del triaje y de lo ya medido para cada asset."""
    entradas = tuple(
        CatalogEntry(
            content_hash=hashes[ruta],
            source=_relativa(ruta, root),
            media_type=MediaType.PHOTO,
            width=sizes[ruta][0],
            height=sizes[ruta][1],
        )
        for ruta in triage.accepted
        if ruta in sizes and ruta in hashes
    )
    apartados = tuple(_a_registro(asset, root) for asset in triage.quarantined)
    return Catalog(root=root, entries=entradas, quarantined=apartados)


def _a_registro(asset: QuarantinedAsset, root: Path) -> QuarantineRecord:
    return QuarantineRecord(
        source=_relativa(asset.path, root), reason=asset.reason, detail=asset.detail
    )


def _relativa(ruta: Path, root: Path) -> str:
    try:
        return ruta.relative_to(root).as_posix()
    except ValueError:
        return ruta.as_posix()


def _a_diccionario(catalog: Catalog) -> dict[str, Any]:
    return {
        "version": catalog.version,
        "root": catalog.root.as_posix(),
        "entries": [
            {
                "content_hash": entrada.content_hash,
                "source": entrada.source,
                "media_type": str(entrada.media_type),
                "width": entrada.width,
                "height": entrada.height,
            }
            for entrada in catalog.entries
        ],
        "quarantined": [
            {
                "source": registro.source,
                "reason": str(registro.reason),
                "detail": registro.detail,
            }
            for registro in catalog.quarantined
        ],
    }


def _desde_diccionario(datos: Any, origen: Path) -> Catalog:
    if not isinstance(datos, dict):
        msg = f"el catálogo debe ser un objeto JSON: {origen}"
        raise InvalidInputError(msg)
    version = datos.get("version")
    if version != CATALOG_VERSION:
        msg = (
            f"versión de catálogo no soportada en {origen}: "
            f"encontrada {version!r}, soportada {CATALOG_VERSION}"
        )
        raise InvalidInputError(msg)
    return Catalog(
        root=Path(_campo(datos, "root", str, origen)),
        entries=tuple(_a_entrada(bruto, origen) for bruto in _lista(datos, "entries", origen)),
        quarantined=tuple(
            _a_apartado(bruto, origen) for bruto in _lista(datos, "quarantined", origen)
        ),
        version=CATALOG_VERSION,
    )


def _lista(datos: dict[str, Any], clave: str, origen: Path) -> list[Any]:
    valor = datos.get(clave, [])
    if not isinstance(valor, list):
        msg = f"el campo '{clave}' del catálogo debe ser una lista: {origen}"
        raise InvalidInputError(msg)
    return valor


def _a_entrada(bruto: Any, origen: Path) -> CatalogEntry:
    if not isinstance(bruto, dict):
        msg = f"cada entrada del catálogo debe ser un objeto: {origen}"
        raise InvalidInputError(msg)
    return CatalogEntry(
        content_hash=_campo(bruto, "content_hash", str, origen),
        source=_campo(bruto, "source", str, origen),
        media_type=MediaType(_campo(bruto, "media_type", str, origen)),
        width=_campo(bruto, "width", int, origen),
        height=_campo(bruto, "height", int, origen),
    )


def _a_apartado(bruto: Any, origen: Path) -> QuarantineRecord:
    if not isinstance(bruto, dict):
        msg = f"cada apartado del catálogo debe ser un objeto: {origen}"
        raise InvalidInputError(msg)
    return QuarantineRecord(
        source=_campo(bruto, "source", str, origen),
        reason=QuarantineReason(_campo(bruto, "reason", str, origen)),
        detail=_campo(bruto, "detail", str, origen),
    )


def _campo[T](bruto: dict[str, Any], clave: str, tipo: type[T], origen: Path) -> T:
    valor = bruto.get(clave)
    if not isinstance(valor, tipo) or (isinstance(valor, bool) and tipo is int):
        msg = f"el campo '{clave}' falta o tiene un tipo incorrecto en {origen}: {valor!r}"
        raise InvalidInputError(msg)
    return valor
