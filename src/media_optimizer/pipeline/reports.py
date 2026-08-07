"""Generación de los reportes: de los datos del workspace a algo que se puede leer.

En simple: las etapas producen datos; aquí esos datos se vuelven una tabla que una
persona puede revisar. El primero es el inventario: una fila por foto con sus
medidas, su orientación y sus advertencias, más la lista de lo apartado con su
causa — la misma estructura de la auditoría que el cliente hacía a mano.

Un reporte **no calcula nada**: si el dato no está en el directorio de trabajo, el
reporte dice qué etapa falta en vez de ejecutarla por su cuenta. Y como el archivo
generado se compara byte a byte entre corridas, no lleva fecha ni hora: dos
generaciones sobre el mismo catálogo producen exactamente el mismo archivo.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from media_optimizer.core import InvalidInputError
from media_optimizer.ingest import Catalog, filesystem, load_catalog
from media_optimizer.logs import get_logger
from media_optimizer.workspace import Workspace

_MARKDOWN = "markdown"
_EXTENSIONES = {"texto": ".txt", _MARKDOWN: ".md"}


@dataclass(frozen=True, slots=True)
class ReportRequest:
    """Lo que todo reporte necesita: de dónde leer y en qué presentación."""

    workspace: Path
    output_format: str


@dataclass(frozen=True, slots=True)
class ReportResult:
    """Un reporte generado: su contenido y dónde quedó escrito."""

    content: str
    written_to: Path


def available_reports() -> frozenset[str]:
    """Los reportes que ya saben generarse en esta versión."""
    return frozenset(_GENERADORES)


def generate_report(name: str, request: ReportRequest) -> ReportResult:
    """Genera el reporte pedido, lo escribe en ``reports/`` y lo devuelve.

    Raises:
        InvalidInputError: si el reporte no existe, el formato no aplica o falta
            la etapa que produce sus datos.
    """
    generador = _GENERADORES.get(name)
    if generador is None:
        msg = f"el reporte '{name}' todavía no está disponible en esta versión"
        raise InvalidInputError(msg)
    extension = _EXTENSIONES.get(request.output_format)
    if extension is None:
        msg = (
            f"el formato '{request.output_format}' no aplica al reporte '{name}'; "
            f"elige entre: {', '.join(sorted(_EXTENSIONES))}"
        )
        raise InvalidInputError(msg)

    contenido = generador(request)
    espacio = Workspace(root=request.workspace)
    espacio.ensure()
    destino = espacio.reports_dir / f"{name}{extension}"
    filesystem.write_bytes(destino, contenido.encode("utf-8"))
    get_logger("pipeline").info(
        "reporte generado", extra={"report": name, "written_to": str(destino)}
    )
    return ReportResult(content=contenido, written_to=destino)


def _inventory(request: ReportRequest) -> str:
    inventario = load_catalog(request.workspace)
    if request.output_format == _MARKDOWN:
        return _inventario_markdown(inventario)
    return _inventario_texto(inventario)


def _inventario_markdown(inventario: Catalog) -> str:
    lineas = [
        "# Inventario del lote",
        "",
        f"Aceptados: **{len(inventario.entries)}** · En cuarentena: "
        f"**{len(inventario.quarantined)}**",
        "",
        "| Archivo | Dimensiones | Orientación | Flags |",
        "|---------|-------------|-------------|-------|",
    ]
    lineas.extend(
        f"| {entrada.source} | {entrada.width}x{entrada.height} "
        f"| {entrada.orientation.value} | {_flags(entrada)} |"
        for entrada in inventario.entries
    )
    if inventario.quarantined:
        lineas += ["", "## Cuarentena", "", "| Archivo | Causa | Detalle |", "|---|---|---|"]
        lineas.extend(
            f"| {registro.source} | {registro.reason.value} | {registro.detail} |"
            for registro in inventario.quarantined
        )
    return "\n".join(lineas) + "\n"


def _inventario_texto(inventario: Catalog) -> str:
    lineas = [
        "INVENTARIO DEL LOTE",
        f"Aceptados: {len(inventario.entries)} · En cuarentena: {len(inventario.quarantined)}",
        "",
    ]
    lineas.extend(
        f"{entrada.source}  {entrada.width}x{entrada.height}  "
        f"{entrada.orientation.value}  {_flags(entrada)}"
        for entrada in inventario.entries
    )
    if inventario.quarantined:
        lineas += ["", "CUARENTENA"]
        lineas.extend(
            f"{registro.source}  [{registro.reason.value}]  {registro.detail}"
            for registro in inventario.quarantined
        )
    return "\n".join(lineas) + "\n"


def _flags(entrada: object) -> str:
    """Las advertencias del asset. Llegan con las etapas de análisis; hoy no hay."""
    del entrada
    return "—"


_GENERADORES: dict[str, Callable[[ReportRequest], str]] = {
    "inventory": _inventory,
}
