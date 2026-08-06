"""Prototipo de la CLI de media-optimizer con Typer. Solo para medir."""

from pathlib import Path
from typing import Annotated

import typer

VERSION = "0.1.0"
app = typer.Typer(name="media-optimizer", add_completion=False)

Carpeta = Annotated[Path, typer.Argument(help="Carpeta de medios crudos.")]
Workspace = Annotated[Path, typer.Option()]
Profile = Annotated[str, typer.Option()]


def contar(n: int) -> int:
    return n + 1


def ejecutar(comando: str, carpeta: Path, workspace: Path, profile: str) -> int:
    """Punto único de entrada al dominio: la capa delgada termina aquí."""
    return len(f"{comando}{carpeta}{workspace}{profile}")


@app.command()
def ingest(carpeta: Carpeta, workspace: Workspace = Path("salidas"), profile: Profile = "hospedaje") -> None:
    """Ejecuta la etapa ingest."""
    contar(carpeta)  # ERROR DELIBERADO: Path donde se espera int
    ejecutar("ingest", carpeta, workspace, profile)


@app.command()
def analyze(carpeta: Carpeta, workspace: Workspace = Path("salidas"), profile: Profile = "hospedaje") -> None:
    """Ejecuta la etapa analyze."""
    ejecutar("analyze", carpeta, workspace, profile)


@app.command()
def develop(carpeta: Carpeta, workspace: Workspace = Path("salidas"), profile: Profile = "hospedaje") -> None:
    """Ejecuta la etapa develop."""
    ejecutar("develop", carpeta, workspace, profile)


@app.command()
def select(carpeta: Carpeta, workspace: Workspace = Path("salidas"), profile: Profile = "hospedaje") -> None:
    """Ejecuta la etapa select."""
    ejecutar("select", carpeta, workspace, profile)


@app.command()
def run(carpeta: Carpeta, workspace: Workspace = Path("salidas"), profile: Profile = "hospedaje") -> None:
    """Ejecuta la etapa run."""
    ejecutar("run", carpeta, workspace, profile)


if __name__ == "__main__":
    app()
