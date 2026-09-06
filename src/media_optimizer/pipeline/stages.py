"""Ejecución de las etapas del pipeline, con su medición incluida.

En simple: aquí es donde una etapa pasa de ser un nombre en el registro a trabajo
hecho. Cada ejecución se mide —cuánto tardó y cuánta memoria llegó a usar— y deja
su ficha, porque sin esa ficha no habría forma de saber por qué un lote fue lento.

La primera etapa que sabe ejecutarse es la ingesta: lee la carpeta del usuario,
aparta lo que no sirve llevando su causa, mide y toma la huella de cada foto, y
escribe el catálogo en el directorio de trabajo. Al final **comprueba** —no
promete— que los archivos originales quedaron byte a byte como estaban.
"""

import json
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import cv2

from media_optimizer.core import (
    CorruptMediaError,
    InvalidInputError,
    MediaOptimizerError,
    OutputFormat,
    OutputIntent,
    QualityReport,
    StageReport,
    Transform,
    Verdict,
)
from media_optimizer.ingest import (
    CatalogEntry,
    DuplicateGroup,
    TriageResult,
    below_native,
    catalog_from_triage,
    compute_content_hash,
    detect_image_format,
    filesystem,
    find_duplicate_groups,
    load_catalog,
    oriented_size,
    read_exif,
    read_image_size_from_path,
    save_catalog,
    scan_input_folder,
    triage_media,
    whatsapp_compression,
)
from media_optimizer.logs import get_logger
from media_optimizer.photo import (
    ExposureThresholds,
    apply_pipeline,
    build_plan,
    exposure_score,
    verdict_for,
)
from media_optimizer.ranking import (
    RankedAsset,
    cover_candidates,
    gallery_order,
    global_score,
    select_by_format,
)
from media_optimizer.vision import (
    blown_highlights_ratio,
    crushed_shadows_ratio,
    decode_image,
    mean_brightness,
)
from media_optimizer.workspace import (
    SourceFingerprint,
    Workspace,
    find_modified_sources,
    safe_output_name,
)


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


# --- etapa analyze -----------------------------------------------------------

ANALYSIS_FILENAME = "analysis.json"
ANALYSIS_VERSION = 1

# Criterio del cliente 0 mientras llega la carga de perfiles desde archivo.
# TODO(HU-131): estos valores pasan al perfil `hospedaje` y se cargan de datos.
_UMBRALES_EXPOSICION = ExposureThresholds(
    brightness_target=128.0,
    crushed_shadows_weight=1.0,
    blown_highlights_weight=1.5,
    publishable_min_score=0.75,
    support_min_score=0.45,
)
_UMBRAL_NEGRO = 26.0
_UMBRAL_QUEMADO = 250.0
_FORMATOS_SALIDA = (
    OutputFormat(intent=OutputIntent.COVER, width=1920, height=1080),
    OutputFormat(intent=OutputIntent.FEED, width=1080, height=1350),
    OutputFormat(intent=OutputIntent.STORY, width=1080, height=1920),
)


def _analyze(request: StageRequest) -> tuple[tuple[str, ...], bool]:
    """Catálogo → análisis de calidad por foto, escrito junto al catálogo."""
    inventario = load_catalog(request.workspace)
    analisis: dict[str, dict[str, object]] = {}
    conteo = {Verdict.PUBLISHABLE: 0, Verdict.SUPPORT: 0, Verdict.DISCARD: 0}
    ilegibles = 0
    for entrada in inventario.entries:
        resultado = _analizar_asset(inventario.root, entrada)
        if resultado is None:
            ilegibles += 1
            continue
        analisis[entrada.content_hash] = resultado
        conteo[Verdict(str(resultado["verdict"]))] += 1

    documento = {"version": ANALYSIS_VERSION, "assets": analisis}
    texto = json.dumps(documento, indent=2, sort_keys=True, ensure_ascii=False)
    destino = request.workspace / ANALYSIS_FILENAME
    filesystem.write_bytes(destino, (texto + "\n").encode("utf-8"))

    resumen = (
        f"Fotos analizadas: {len(analisis)}",
        f"  publicables: {conteo[Verdict.PUBLISHABLE]}",
        f"  de apoyo: {conteo[Verdict.SUPPORT]}",
        f"  para descartar: {conteo[Verdict.DISCARD]}",
        *((f"  ilegibles al decodificar: {ilegibles}",) if ilegibles else ()),
        f"Análisis escrito en: {destino}",
    )
    return resumen, ilegibles > 0


def _analizar_asset(root: Path, entrada: CatalogEntry) -> dict[str, object] | None:
    """Mide, califica y da veredicto a una foto; ``None`` si no se pudo decodificar."""
    ruta = root / entrada.source
    try:
        imagen = decode_image(ruta)
    except CorruptMediaError:
        return None

    brillo = mean_brightness(imagen)
    negro = crushed_shadows_ratio(imagen, _UMBRAL_NEGRO)
    quemado = blown_highlights_ratio(imagen, _UMBRAL_QUEMADO)

    exif = read_exif(ruta)
    flags: list[str] = []
    if whatsapp_compression(
        entrada.source,
        filesystem.file_size(ruta),
        entrada.width * entrada.height,
        exif.is_present,
    ):
        flags.append("whatsapp_compressed")
    cortas = below_native(entrada.width, entrada.height, _FORMATOS_SALIDA)
    flags.extend(f"below_native_{intencion.value}" for intencion in cortas)

    score = exposure_score(brillo, negro, quemado, _UMBRALES_EXPOSICION)
    veredicto, causas = verdict_for(score, tuple(flags), _UMBRALES_EXPOSICION)

    reporte = QualityReport(
        metrics={
            "mean_brightness": round(brillo, 2),
            "crushed_shadows_ratio": round(negro, 4),
            "blown_highlights_ratio": round(quemado, 4),
            "exposure_score": round(score, 4),
        },
        flags=tuple(flags),
        verdict=veredicto,
    )
    return {
        "metrics": dict(reporte.metrics),
        "flags": list(reporte.flags),
        "verdict": reporte.verdict.value,
        "causes": list(causas),
    }


_EJECUTORES["analyze"] = _analyze


# --- etapa develop -----------------------------------------------------------

DEVELOP_FILENAME = "develop.json"
DERIVED_DIRNAME = "derived"
_CALIDAD_JPEG = 92

# El plan de revelado del cliente 0 mientras llega el perfil como archivo.
# TODO(HU-135): el orden y los valores pasan a la plantilla del perfil.
_PLAN_REVELADO = (
    Transform(name="clahe", params={"clip_limit": 2.0, "tile_size": 8}),
    Transform(name="shadows", params={"amount": 0.35}),
    Transform(name="exposure", params={"target_brightness": 128}),
    Transform(name="white_balance", params={"warmth": 0.06}),
    Transform(name="saturation", params={"factor": 1.06, "max_factor": 1.06}),
)


def _develop(request: StageRequest) -> tuple[tuple[str, ...], bool]:
    """Analizadas → reveladas en ``derived/``, con antes/después y historial."""
    inventario = load_catalog(request.workspace)
    ruta_analisis = request.workspace / ANALYSIS_FILENAME
    if not filesystem.exists(ruta_analisis):
        msg = (
            f"no hay análisis en '{request.workspace}': "
            "ejecuta primero: media-optimizer run analyze"
        )
        raise InvalidInputError(msg)
    analisis = json.loads(filesystem.read_bytes(ruta_analisis).decode("utf-8"))["assets"]

    plan = build_plan(_PLAN_REVELADO)
    destino_dir = request.workspace / DERIVED_DIRNAME
    filesystem.make_directory(destino_dir)

    reveladas: dict[str, dict[str, object]] = {}
    usados: set[str] = set()
    descartadas = ilegibles = 0
    for entrada in inventario.entries:
        ficha = analisis.get(entrada.content_hash)
        if ficha is None or ficha["verdict"] == Verdict.DISCARD.value:
            descartadas += 1
            continue
        if entrada.content_hash in reveladas:
            continue  # copias del mismo contenido: se revela una sola vez
        resultado = _revelar_asset(inventario.root, entrada, plan, destino_dir, usados)
        if resultado is None:
            ilegibles += 1
            continue
        reveladas[entrada.content_hash] = resultado

    documento = {"version": 1, "plan": [_paso_a_dict(p) for p in plan], "assets": reveladas}
    texto = json.dumps(documento, indent=2, sort_keys=True, ensure_ascii=False)
    filesystem.write_bytes(request.workspace / DEVELOP_FILENAME, (texto + "\n").encode("utf-8"))

    resumen = (
        f"Fotos reveladas: {len(reveladas)}",
        f"  descartadas por veredicto: {descartadas}",
        *((f"  ilegibles: {ilegibles}",) if ilegibles else ()),
        f"Salidas en: {destino_dir}",
    )
    return resumen, ilegibles > 0


def _revelar_asset(
    root: Path,
    entrada: CatalogEntry,
    plan: tuple[Transform, ...],
    destino_dir: Path,
    usados: set[str],
) -> dict[str, object] | None:
    ruta = root / entrada.source
    try:
        imagen = decode_image(ruta)
    except CorruptMediaError:
        return None
    antes = round(mean_brightness(imagen), 2)
    revelada, historial = apply_pipeline(imagen, plan)
    despues = round(mean_brightness(revelada), 2)

    nombre = safe_output_name(Path(entrada.source).name, frozenset(usados))
    usados.add(nombre)
    ok, codificada = cv2.imencode(".jpg", revelada, [cv2.IMWRITE_JPEG_QUALITY, _CALIDAD_JPEG])
    if not ok:  # pragma: no cover - imencode no falla sobre uint8 valido
        return None
    # imencode no escribe EXIF: la salida nace sin GPS ni metadatos personales.
    filesystem.write_bytes(destino_dir / nombre, codificada.tobytes())
    return {
        "output": nombre,
        "brightness_before": antes,
        "brightness_after": despues,
        "history": [_paso_a_dict(paso) for paso in historial],
    }


def _paso_a_dict(paso: Transform) -> dict[str, object]:
    return {"name": paso.name, "params": dict(paso.params)}


_EJECUTORES["develop"] = _develop


# --- etapa select ------------------------------------------------------------

SELECTION_FILENAME = "selection.json"
_TOP_PORTADA = 5

# Pesos del score global mientras llega el perfil como archivo.
# TODO(HU-134): pasan al perfil, por intención de salida.
_PESOS_SCORE = {"exposure_score": 1.0}
_INTENCIONES = tuple(formato.intent.value for formato in _FORMATOS_SALIDA)


def _select(request: StageRequest) -> tuple[tuple[str, ...], bool]:
    """Analizadas → portada, galería y selección por formato, deterministas."""
    inventario = load_catalog(request.workspace)
    ruta_analisis = request.workspace / ANALYSIS_FILENAME
    if not filesystem.exists(ruta_analisis):
        msg = (
            f"no hay análisis en '{request.workspace}': "
            "ejecuta primero: media-optimizer run analyze"
        )
        raise InvalidInputError(msg)
    analisis = json.loads(filesystem.read_bytes(ruta_analisis).decode("utf-8"))["assets"]

    vistos: set[str] = set()
    fotos: list[RankedAsset] = []
    for entrada in inventario.entries:
        ficha = analisis.get(entrada.content_hash)
        if ficha is None or entrada.content_hash in vistos:
            continue
        vistos.add(entrada.content_hash)
        fotos.append(
            RankedAsset(
                content_hash=entrada.content_hash,
                source=entrada.source,
                score=global_score(
                    {k: float(v) for k, v in ficha["metrics"].items()}, _PESOS_SCORE
                ),
                verdict=Verdict(str(ficha["verdict"])),
                flags=tuple(ficha["flags"]),
                width=entrada.width,
                height=entrada.height,
            )
        )
    lote = tuple(fotos)

    portada = cover_candidates(lote, top=_TOP_PORTADA)
    galeria = gallery_order(lote)
    por_formato = select_by_format(lote, _INTENCIONES)

    documento = {
        "version": 1,
        "cover_candidates": [a.source for a in portada],
        "gallery": [a.source for a in galeria],
        "by_format": {
            intencion: [a.source for a in fotos_formato]
            for intencion, fotos_formato in sorted(por_formato.items())
        },
    }
    texto = json.dumps(documento, indent=2, sort_keys=True, ensure_ascii=False)
    filesystem.write_bytes(request.workspace / SELECTION_FILENAME, (texto + "\n").encode("utf-8"))

    resumen = (
        f"Candidatas a portada: {len(portada)}",
        f"Galería ordenada: {len(galeria)} fotos",
        *(
            f"  {intencion}: {len(fotos_formato)} elegibles"
            for intencion, fotos_formato in sorted(por_formato.items())
        ),
        f"Selección escrita en: {request.workspace / SELECTION_FILENAME}",
    )
    return resumen, False


# --- secuencia all: el pipeline completo con un comando ----------------------

_SECUENCIA = ("ingest", "analyze", "develop", "select")


def _all(request: StageRequest) -> tuple[tuple[str, ...], bool]:
    """Ejecuta la secuencia completa; una etapa degradada no detiene a las demás."""
    lineas: list[str] = []
    parcial = False
    for nombre in _SECUENCIA:
        resultado = execute_stage(nombre, request)
        parcial = parcial or resultado.partial
        lineas.append(f"── {nombre} ──")
        lineas.extend(resultado.summary)
    return tuple(lineas), parcial


_EJECUTORES["select"] = _select
_EJECUTORES["all"] = _all
