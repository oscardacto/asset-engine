"""Comando ``report``: muestra lo que el pipeline ya produjo.

En simple: ``report inventory`` dice qué hay en el lote, ``report analysis`` cómo
salió la calidad. **No calcula nada**: si el dato no está en el directorio de
trabajo, avisa de que falta esa etapa en vez de ejecutarla por su cuenta.
"""

import argparse
from dataclasses import dataclass
from enum import StrEnum

from media_optimizer.cli.console import Console
from media_optimizer.cli.context import RunContext
from media_optimizer.cli.exit_codes import ExitCode
from media_optimizer.core.errors import InvalidInputError
from media_optimizer.ingest import filesystem
from media_optimizer.pipeline import find_report, report_names

DESTINOS = ("kind", "output_format")
CATALOGO = "catalogo.json"


class OutputFormat(StrEnum):
    """Cómo se presenta el reporte."""

    TEXT = "texto"
    MARKDOWN = "markdown"
    JSONL = "jsonl"


@dataclass(frozen=True, slots=True)
class ReportArgs:
    """Lo que se le pidió al comando, ya con tipos verificables."""

    kind: str
    output_format: OutputFormat


def configure(parser: argparse.ArgumentParser) -> None:
    """Declara los argumentos del comando."""
    parser.add_argument(
        "kind",
        choices=report_names(),
        help="Reporte a mostrar.",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=tuple(formato.value for formato in OutputFormat),
        default=OutputFormat.TEXT.value,
        help="Presentación del reporte.",
    )


def parse(namespace: argparse.Namespace) -> ReportArgs:
    """Convierte el ``Namespace`` sin tipos en el contrato del comando."""
    return ReportArgs(
        kind=str(namespace.kind),
        output_format=OutputFormat(namespace.output_format),
    )


def execute(namespace: argparse.Namespace, context: RunContext, console: Console) -> ExitCode:
    """Muestra el reporte pedido, si el trabajo que lo produce ya se hizo."""
    args = parse(namespace)
    if not filesystem.exists(context.workspace / CATALOGO):
        msg = (
            f"No hay nada que reportar en '{context.workspace}': "
            "todavía no se ha ejecutado la ingesta.\n"
            "  Ejecuta primero: media-optimizer run ingest <carpeta>"
        )
        raise InvalidInputError(msg)

    reporte = find_report(args.kind)
    if reporte is None or not reporte.available:
        console.fail(f"El reporte '{args.kind}' todavía no está disponible en esta versión.")
        return ExitCode.FAILURE

    console.say(f"Reporte '{args.kind}' ({args.output_format.value})")
    return ExitCode.OK
