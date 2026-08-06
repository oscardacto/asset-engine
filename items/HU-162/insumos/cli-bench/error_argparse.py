"""Prototipo de la CLI de media-optimizer con argparse. Solo para medir."""

import argparse
from pathlib import Path

COMANDOS = ("ingest", "analyze", "develop", "select", "run")
VERSION = "0.1.0"


def ejecutar(comando: str, carpeta: Path, workspace: Path, profile: str) -> int:
    """Punto único de entrada al dominio: la capa delgada termina aquí."""
    return len(f"{comando}{carpeta}{workspace}{profile}")


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


def contar(n: int) -> int:
    return n + 1


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    contar(args.carpeta)  # ERROR DELIBERADO: Path donde se espera int
    return ejecutar(args.comando, args.carpeta, args.workspace, args.profile)


if __name__ == "__main__":
    raise SystemExit(main())
