"""Los comandos que la CLI ofrece, declarados uno a uno.

En simple: son tres —hacer el trabajo, leer lo que salió, corregir a mano—, y la
lista está escrita aquí a la vista. Nada se descubre solo recorriendo carpetas: un
comando existe porque está en esta tupla, y así el conjunto no depende del orden en
que el sistema devuelva los archivos.

Lo que sí crece con el tiempo son las **etapas** y los **reportes**, y esos viven
en el registro del pipeline. Por eso estos tres no aumentan aunque el programa
aprenda a hacer cosas nuevas.
"""

import argparse
from collections.abc import Callable
from dataclasses import dataclass

from media_optimizer.cli.commands import label, report, run
from media_optimizer.cli.console import Console
from media_optimizer.cli.context import RunContext
from media_optimizer.cli.exit_codes import ExitCode


@dataclass(frozen=True, slots=True)
class Command:
    """Un comando: su nombre, su ayuda, cómo se declara y cómo se ejecuta."""

    name: str
    help: str
    configure: Callable[[argparse.ArgumentParser], None]
    execute: Callable[[argparse.Namespace, RunContext, Console], ExitCode]
    arg_destinations: tuple[str, ...]
    args_contract: type


COMMANDS: tuple[Command, ...] = (
    Command(
        name="run",
        help="Ejecuta una etapa del trabajo sobre tus medios.",
        configure=run.configure,
        execute=run.execute,
        arg_destinations=run.DESTINOS,
        args_contract=run.RunArgs,
    ),
    Command(
        name="report",
        help="Muestra lo que el pipeline ya produjo.",
        configure=report.configure,
        execute=report.execute,
        arg_destinations=report.DESTINOS,
        args_contract=report.ReportArgs,
    ),
    Command(
        name="label",
        help="Confirma o corrige a mano lo que la máquina propuso.",
        configure=label.configure,
        execute=label.execute,
        arg_destinations=label.DESTINOS,
        args_contract=label.LabelArgs,
    ),
)


def find_command(name: str) -> Command | None:
    """El comando que se llama así, o ``None`` si no existe."""
    return next((comando for comando in COMMANDS if comando.name == name), None)


__all__ = ["COMMANDS", "Command", "find_command"]
