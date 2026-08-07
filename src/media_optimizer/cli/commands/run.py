"""Comando ``run``: ejecuta una etapa del trabajo.

En simple: ``run ingest`` lee la carpeta, ``run analyze`` mide la calidad,
``run all`` hace todo seguido. Qué etapas existen no se decide aquí — se le
pregunta al registro del pipeline, para que añadir una etapa nueva no obligue a
tocar la línea de comandos.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path

from media_optimizer.cli.console import Console
from media_optimizer.cli.context import RunContext
from media_optimizer.cli.exit_codes import ExitCode
from media_optimizer.logs import get_logger
from media_optimizer.pipeline import find_stage, stage_names
from media_optimizer.pipeline.stages import StageRequest, execute_stage

DESTINOS = ("stage", "source", "force", "resume")


@dataclass(frozen=True, slots=True)
class RunArgs:
    """Lo que se le pidió al comando, ya con tipos verificables."""

    stage: str
    source: Path | None
    force: bool
    resume: bool


def configure(parser: argparse.ArgumentParser) -> None:
    """Declara los argumentos del comando."""
    parser.add_argument(
        "stage",
        choices=stage_names(),
        help="Etapa a ejecutar.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=None,
        metavar="ORIGEN",
        help="Carpeta de medios crudos. Solo la usa la etapa de ingesta.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rehace el trabajo aunque ya exista hecho.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Retoma donde quedó en vez de empezar de cero.",
    )


def parse(namespace: argparse.Namespace) -> RunArgs:
    """Convierte el ``Namespace`` sin tipos en el contrato del comando."""
    source = namespace.source
    return RunArgs(
        stage=str(namespace.stage),
        source=Path(source) if source is not None else None,
        force=bool(namespace.force),
        resume=bool(namespace.resume),
    )


def execute(namespace: argparse.Namespace, context: RunContext, console: Console) -> ExitCode:
    """Ejecuta la etapa pedida y muestra su resumen."""
    args = parse(namespace)
    etapa = find_stage(args.stage)
    if etapa is None or not etapa.available:
        console.fail(
            f"La etapa '{args.stage}' todavía no está disponible en esta versión.\n"
            f"  {etapa.description if etapa else ''}"
        )
        get_logger("cli").warning(
            "etapa no disponible", extra={"stage": args.stage, "profile": context.profile}
        )
        return ExitCode.FAILURE

    peticion = StageRequest(
        workspace=context.workspace, profile=context.profile, source=args.source
    )
    resultado = execute_stage(args.stage, peticion)
    for linea in resultado.summary:
        console.say(linea)
    return ExitCode.PARTIAL if resultado.partial else ExitCode.OK
