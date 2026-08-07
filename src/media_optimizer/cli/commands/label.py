"""Comando ``label``: la persona confirma o corrige lo que la máquina propuso.

En simple: el programa propone a qué ambiente pertenece cada foto —cocina,
balcón, alcoba— y aquí es donde tú lo confirmas o lo cambias. Lo que decidas se
guarda aparte y **sobrevive a volver a ingerir la carpeta**, para que no haya que
repetirlo cada vez.

No es una etapa del pipeline y por eso no vive bajo ``run``: lo decide un humano, y
su resultado es una entrada del pipeline, no un producto suyo.
"""

import argparse
from dataclasses import dataclass

from media_optimizer.cli.console import Console
from media_optimizer.cli.context import RunContext
from media_optimizer.cli.exit_codes import ExitCode

DESTINOS = ("asset", "accept_all")


@dataclass(frozen=True, slots=True)
class LabelArgs:
    """Lo que se le pidió al comando, ya con tipos verificables."""

    asset: str | None
    accept_all: bool


def configure(parser: argparse.ArgumentParser) -> None:
    """Declara los argumentos del comando."""
    parser.add_argument(
        "--asset",
        default=None,
        metavar="HUELLA",
        help="Etiqueta solo este asset. Sin esto, recorre el lote completo.",
    )
    parser.add_argument(
        "--accept-all",
        action="store_true",
        help="Acepta todas las propuestas sin preguntar una por una.",
    )


def parse(namespace: argparse.Namespace) -> LabelArgs:
    """Convierte el ``Namespace`` sin tipos en el contrato del comando."""
    asset = namespace.asset
    return LabelArgs(
        asset=str(asset) if asset is not None else None,
        accept_all=bool(namespace.accept_all),
    )


def execute(namespace: argparse.Namespace, _context: RunContext, console: Console) -> ExitCode:
    """Abre el etiquetado asistido.

    Recibe el contexto aunque todavía no lo use: la firma es la misma para los tres
    comandos, y es lo que permite despacharlos sin distinguir cuál es cuál.
    """
    parse(namespace)
    console.fail("El etiquetado asistido todavía no está disponible en esta versión.")
    return ExitCode.FAILURE
