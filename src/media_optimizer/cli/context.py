"""Lo que vale para todo el run: dónde escribir, con qué criterio y cuánto contar.

En simple: el directorio de salida y el perfil de negocio no son parámetros de una
etapa concreta, son el contexto de toda la ejecución. Por eso se escriben una vez,
antes del comando, y no hay que repetirlos al encadenar varios.

Ninguna opción trae su valor por defecto desde el parser: las que no se indican
llegan aquí como "sin indicar", y es en este punto donde se resuelven. Esa
distinción entre *no lo dijo* y *lo dijo con el valor habitual* es la que permitirá
que un archivo de configuración se aplique por debajo de la línea de comandos.
"""

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

WORKSPACE_POR_DEFECTO = Path("salidas")
PERFIL_POR_DEFECTO = "hospedaje"
NIVEL_POR_DEFECTO = "INFO"
NIVELES = ("DEBUG", "INFO", "WARNING", "ERROR")

DESTINOS_GLOBALES = ("workspace", "profile", "log_level", "log_file", "quiet")


@dataclass(frozen=True, slots=True)
class RunContext:
    """Contexto de la ejecución completa, con los valores ya resueltos."""

    workspace: Path
    profile: str
    log_level: str
    log_file: Path | None
    quiet: bool

    def log_level_number(self) -> int:
        """El nivel como número, que es lo que espera el rastro estructurado."""
        return logging.getLevelNamesMapping()[self.log_level]


def add_global_arguments(parser: argparse.ArgumentParser) -> None:
    """Declara las opciones que valen para cualquier comando."""
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        metavar="RUTA",
        help=f"Directorio donde se escriben las salidas (por defecto: {WORKSPACE_POR_DEFECTO}).",
    )
    parser.add_argument(
        "--profile",
        default=None,
        metavar="NOMBRE",
        help=f"Perfil de negocio a aplicar (por defecto: {PERFIL_POR_DEFECTO}).",
    )
    parser.add_argument(
        "--log-level",
        choices=NIVELES,
        default=None,
        help=f"Detalle del rastro estructurado (por defecto: {NIVEL_POR_DEFECTO}).",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        metavar="RUTA",
        help="Además de la consola, deja el rastro en este archivo.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Muestra solo los fallos.",
    )


def parse_context(namespace: argparse.Namespace) -> RunContext:
    """Convierte las opciones globales en un contexto con tipos verificables.

    Es la frontera: a partir de aquí nadie vuelve a tocar el ``Namespace``.
    """
    # TODO(HU-155): los valores por defecto pasan a config/ cuando exista, y se
    # resuelven aquí mismo con la precedencia argumento > entorno > archivo > default.
    workspace = namespace.workspace
    profile = namespace.profile
    log_level = namespace.log_level
    log_file = namespace.log_file
    return RunContext(
        workspace=Path(workspace) if workspace is not None else WORKSPACE_POR_DEFECTO,
        profile=str(profile) if profile is not None else PERFIL_POR_DEFECTO,
        log_level=str(log_level) if log_level is not None else NIVEL_POR_DEFECTO,
        log_file=Path(log_file) if log_file is not None else None,
        quiet=bool(namespace.quiet),
    )
