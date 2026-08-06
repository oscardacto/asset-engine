"""Comparación entre dos estados del mismo lote: qué cambió desde la última vez.

En simple: si vuelves a ingerir la misma carpeta, esto dice qué hay de nuevo,
qué sigue igual, qué desapareció y qué simplemente cambió de nombre o de sitio.
Sirve para no repetir trabajo ya hecho y para no perder lo que hayas anotado a
mano sobre una foto solo porque la moviste de carpeta.

La comparación es por **contenido**, no por nombre: renombrar una foto no la
convierte en otra.
"""

from dataclasses import dataclass
from enum import StrEnum

from media_optimizer.ingest.catalog import Catalog, CatalogEntry


class AssetChange(StrEnum):
    """Qué le pasó a un asset entre el catálogo anterior y el actual."""

    NEW = "new"
    UNCHANGED = "unchanged"
    MOVED = "moved"
    REMOVED = "removed"


@dataclass(frozen=True, slots=True)
class MovedAsset:
    """Un asset que sigue estando, pero en otro sitio o con otro nombre."""

    content_hash: str
    previous_source: str
    current_source: str


@dataclass(frozen=True, slots=True)
class ReingestPlan:
    """Reparto de los assets según lo que cambió desde la ingesta anterior."""

    new: tuple[CatalogEntry, ...] = ()
    unchanged: tuple[CatalogEntry, ...] = ()
    moved: tuple[MovedAsset, ...] = ()
    removed: tuple[CatalogEntry, ...] = ()

    @property
    def has_changes(self) -> bool:
        """Indica si hay algo que procesar o registrar."""
        return bool(self.new or self.moved or self.removed)


def plan_reingest(previous: Catalog, current: Catalog) -> ReingestPlan:
    """Compara dos catálogos del mismo lote y reparte los assets por lo que cambió."""
    antes = _por_hash(previous)
    ahora = _por_hash(current)

    nuevos: list[CatalogEntry] = []
    iguales: list[CatalogEntry] = []
    movidos: list[MovedAsset] = []

    for huella, entradas in ahora.items():
        previas = antes.get(huella)
        if previas is None:
            nuevos.extend(entradas)
            continue
        rutas_previas = {entrada.source for entrada in previas}
        for entrada in entradas:
            if entrada.source in rutas_previas:
                iguales.append(entrada)
            else:
                movidos.append(
                    MovedAsset(
                        content_hash=huella,
                        previous_source=sorted(rutas_previas)[0],
                        current_source=entrada.source,
                    )
                )

    desaparecidos = [
        entrada for huella, entradas in antes.items() if huella not in ahora for entrada in entradas
    ]

    return ReingestPlan(
        new=tuple(sorted(nuevos, key=lambda e: e.source)),
        unchanged=tuple(sorted(iguales, key=lambda e: e.source)),
        moved=tuple(sorted(movidos, key=lambda m: m.current_source)),
        removed=tuple(sorted(desaparecidos, key=lambda e: e.source)),
    )


def _por_hash(catalog: Catalog) -> dict[str, list[CatalogEntry]]:
    agrupado: dict[str, list[CatalogEntry]] = {}
    for entrada in catalog.entries:
        agrupado.setdefault(entrada.content_hash, []).append(entrada)
    return agrupado
