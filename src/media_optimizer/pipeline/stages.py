"""Ejecución de las etapas del pipeline, con su medición incluida.

En simple: aquí es donde una etapa pasa de ser un nombre en el registro a trabajo
hecho. Cada ejecución se mide —cuánto tardó y cuánta memoria llegó a usar— y deja
su ficha, porque sin esa ficha no habría forma de saber por qué un lote fue lento.

La primera etapa que sabe ejecutarse es la ingesta: lee la carpeta del usuario,
aparta lo que no sirve llevando su causa, mide y toma la huella de cada foto, y
escribe el catálogo en el directorio de trabajo. Al final **comprueba** —no
promete— que los archivos originales quedaron byte a byte como estaban.
"""

import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from media_optimizer.core import InvalidInputError, MediaOptimizerError, StageReport
from media_optimizer.ingest import (
    DuplicateGroup,
    TriageResult,
    catalog_from_triage,
    compute_content_hash,
    detect_image_format,
    find_duplicate_groups,
    oriented_size,
    read_exif,
    read_image_size_from_path,
    save_catalog,
    scan_input_folder,
    triage_media,
)
from media_optimizer.logs import get_logger
from media_optimizer.workspace import SourceFingerprint, Workspace, find_modified_sources


@dataclass(frozen=True, slots=True)
class StageRequest:
    """Lo que toda etapa recibe: dónde escribir, con qué criterio y desde dónde."""

    workspace: Path
    profile: str
    source: Path | None = None


@dataclass(frozen=True, slots=True)
class StageOutcome:
    """Lo que una etapa devuelve: su ficha medida, el resumen legible y cómo acabó."""

    report: StageReport
    summary: tuple[str, ...]
    partial: bool


def available_stages() -> frozenset[str]:
    """Las etapas que ya saben ejecutarse en esta versión."""
    return frozenset(_EJECUTORES)


def execute_stage(name: str, request: StageRequest) -> StageOutcome:
    """Ejecuta la etapa midiendo tiempo y memoria, y deja su ficha en el rastro.

    Raises:
        InvalidInputError: si la etapa no existe o aún no sabe ejecutarse.
    """
    ejecutor = _EJECUTORES.get(name)
    if ejecutor is None:
        msg = f"la etapa '{name}' todavía no está disponible en esta versión"
        raise InvalidInputError(msg)

    tracemalloc.start()
    inicio = time.perf_counter()
    try:
        resumen, parcial = ejecutor(request)
    finally:
        _, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    duracion = time.perf_counter() - inicio

    ficha = StageReport(stage=name, duration_seconds=duracion, peak_memory_bytes=pico)
    get_logger("pipeline").info(
        "etapa terminada",
        extra={
            "stage": name,
            "duration_seconds": round(duracion, 3),
            "peak_memory_bytes": pico,
            "partial": parcial,
        },
    )
    return StageOutcome(report=ficha, summary=resumen, partial=parcial)


def _ingest(request: StageRequest) -> tuple[tuple[str, ...], bool]:
    """Carpeta del usuario → catálogo en el workspace, sin tocar los originales."""
    if request.source is None:
        msg = "la etapa de ingesta necesita la carpeta de origen: run ingest <carpeta>"
        raise InvalidInputError(msg)

    rutas = scan_input_folder(request.source)
    triaje = triage_media(rutas)

    medidas: dict[Path, tuple[int, int]] = {}
    huellas: dict[Path, str] = {}
    for ruta in triaje.accepted:
        medidas[ruta] = _medidas_orientadas(ruta)
        huellas[ruta] = compute_content_hash(ruta)

    espacio = Workspace(root=request.workspace)
    espacio.ensure()
    inventario = catalog_from_triage(request.source, triaje, medidas, huellas)
    destino = save_catalog(inventario, espacio.root)

    _verificar_originales_intactos(huellas)

    duplicados = find_duplicate_groups(triaje.accepted)
    return _resumen(rutas, triaje, duplicados, destino), bool(triaje.quarantined)


def _medidas_orientadas(ruta: Path) -> tuple[int, int]:
    """Medidas en píxeles ya enderezadas según la orientación EXIF."""
    formato = detect_image_format(ruta)
    if formato is None:
        msg = f"el triaje aceptó un archivo sin formato reconocible: {ruta}"
        raise MediaOptimizerError(msg)
    tamano = read_image_size_from_path(ruta, formato)
    if tamano is None:
        msg = f"el triaje aceptó un archivo sin medidas legibles: {ruta}"
        raise MediaOptimizerError(msg)
    exif = read_exif(ruta)
    final = oriented_size(tamano, exif.orientation)
    return (final.width, final.height)


def _verificar_originales_intactos(huellas: dict[Path, str]) -> None:
    """Comprueba con la huella ya calculada que ningún original cambió."""
    previa = SourceFingerprint(
        hashes=tuple(sorted((str(ruta), huella) for ruta, huella in huellas.items()))
    )
    alterados = find_modified_sources(previa)
    if alterados:
        listado = ", ".join(alterados)
        msg = f"los archivos de origen cambiaron durante la ingesta: {listado}"
        raise MediaOptimizerError(msg)


def _resumen(
    rutas: tuple[Path, ...],
    triaje: TriageResult,
    duplicados: tuple[DuplicateGroup, ...],
    destino: Path,
) -> tuple[str, ...]:
    lineas = [
        f"Archivos encontrados: {len(rutas)}",
        f"Aceptados al catálogo: {len(triaje.accepted)}",
        f"Apartados a cuarentena: {len(triaje.quarantined)}",
    ]
    causas: dict[str, int] = {}
    for apartado in triaje.quarantined:
        causas[apartado.reason.value] = causas.get(apartado.reason.value, 0) + 1
    lineas.extend(f"  - {causa}: {cuantos}" for causa, cuantos in sorted(causas.items()))
    if duplicados:
        copias = sum(len(grupo.paths) - 1 for grupo in duplicados)
        lineas.append(f"Contenido repetido: {copias} copias en {len(duplicados)} grupos")
    lineas.append(f"Catálogo escrito en: {destino}")
    return tuple(lineas)


_EJECUTORES: dict[str, Callable[[StageRequest], tuple[tuple[str, ...], bool]]] = {
    "ingest": _ingest,
}
