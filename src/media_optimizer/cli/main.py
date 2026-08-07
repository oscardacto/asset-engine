"""Punto de entrada de la línea de comandos.

En simple: aquí llega lo que escribiste en la terminal, se comprueba que tenga
sentido, se convierte en datos con forma conocida y se le pasa al programa. Al
terminar, traduce el resultado a un número que dice cómo fue — para que puedas
encadenar comandos en un script y saber si seguir.

Es una capa de traducción y nada más: **ninguna decisión sobre tus fotos se toma
aquí**. Los criterios viven en el perfil de negocio y el trabajo en el pipeline.
"""

import argparse
from collections.abc import Sequence

from media_optimizer import __version__
from media_optimizer.cli.commands import COMMANDS, find_command
from media_optimizer.cli.console import Console
from media_optimizer.cli.context import add_global_arguments, parse_context
from media_optimizer.cli.errors import translate
from media_optimizer.cli.exit_codes import ExitCode
from media_optimizer.core.errors import MediaOptimizerError
from media_optimizer.logs import configure_logging, get_logger

PROGRAMA = "media-optimizer"
DESCRIPCION = (
    "Convierte fotos y videos crudos en contenido listo para publicar. "
    "Local, reproducible y sin tocar jamás tus archivos originales."
)
DESTINO_COMANDO = "command"


def build_parser() -> argparse.ArgumentParser:
    """Arma el parser completo: opciones globales y los tres comandos."""
    parser = argparse.ArgumentParser(prog=PROGRAMA, description=DESCRIPCION)
    parser.add_argument("--version", action="version", version=f"{PROGRAMA} {__version__}")
    add_global_arguments(parser)

    subcomandos = parser.add_subparsers(dest=DESTINO_COMANDO, metavar="COMANDO")
    for comando in COMMANDS:
        subparser = subcomandos.add_parser(comando.name, help=comando.help)
        comando.configure(subparser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Ejecuta la CLI y devuelve el código de salida.

    Acepta los argumentos como lista para que las pruebas puedan invocarla sin
    lanzar un proceso aparte.
    """
    parser = build_parser()
    namespace = parser.parse_args(argv)

    nombre = getattr(namespace, DESTINO_COMANDO, None)
    if nombre is None:
        parser.print_help()
        return int(ExitCode.USAGE)

    context = parse_context(namespace)
    configure_logging(level=context.log_level_number(), log_file=context.log_file)
    console = Console(quiet=context.quiet)

    comando = find_command(str(nombre))
    if comando is None:  # pragma: no cover - argparse lo impide antes de llegar aquí
        parser.print_help()
        return int(ExitCode.USAGE)

    try:
        return int(comando.execute(namespace, context, console))
    except MediaOptimizerError as error:
        mensaje, codigo = translate(error)
        console.fail(mensaje)
        get_logger("cli").error(mensaje, extra={"command": comando.name, "exit_code": int(codigo)})
        return int(codigo)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
