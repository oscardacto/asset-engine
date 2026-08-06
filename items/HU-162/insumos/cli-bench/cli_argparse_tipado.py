"""Prototipo con argparse + frontera tipada explícita. Solo para medir."""

import argparse
from dataclasses import dataclass
from pathlib import Path

COMANDOS = ("ingest", "analyze", "develop", "select", "run")
VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class Invocacion:
    """Lo que el usuario pidió, ya con tipos verificables."""

    comando: str
    carpeta: Path
    workspace: Path
    profile: str


def ejecutar(invocacion: Invocacion) -> int:
    """Punto único de entrada al dominio: la capa delgada termina aquí."""
    return len(f"{invocacion.comando}{invocacion.carpeta}")


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="media-optimizer")
    parser.add_argument("--version", action="version", version=VERSION)
    subcomandos = parser.add_subparsers(dest="comando", required=True)
    for nombre in COMANDOS:
        sub = subcomandos.add_parser(nombre, help=f"Ejecuta la etapa {nombre}.")
        sub.add_argument("carpeta", type=Path, help="Carpeta de medios crudos.")
        sub.add_argument("--workspace", type=Path, default=Path("salidas"))
        sub.add_argument("--profile", default="hospedaje")
    return parser


def leer(argv: list[str] | None = None) -> Invocacion:
    """Convierte el Namespace sin tipos en un dato tipado: la frontera está aquí."""
    args = construir_parser().parse_args(argv)
    return Invocacion(
        comando=str(args.comando),
        carpeta=Path(args.carpeta),
        workspace=Path(args.workspace),
        profile=str(args.profile),
    )


def main(argv: list[str] | None = None) -> int:
    return ejecutar(leer(argv))


if __name__ == "__main__":
    raise SystemExit(main())
