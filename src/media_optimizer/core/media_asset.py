"""Contrato ``MediaAsset``: el sustantivo central del dominio (HU-157).

Dominio puro — sin IO: ``source`` es un valor :class:`pathlib.Path` y este módulo
jamás toca el filesystem. Las violaciones de contrato fallan rápido con
``ValueError``: son bugs del llamador, no datos hostiles del usuario (esos los
maneja la ingesta, E1).
"""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class MediaType(StrEnum):
    """Tipo de medio soportado por el pipeline."""

    PHOTO = "photo"
    VIDEO = "video"


class Orientation(StrEnum):
    """Orientación derivada de las dimensiones en píxeles."""

    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    SQUARE = "square"


@dataclass(frozen=True, slots=True)
class MediaAsset:
    """Asset catalogado: tipo (foto/video), dimensiones, hash de contenido y origen.

    Contrato inmutable con igualdad por valor. ``source`` apunta al archivo
    original —que jamás se modifica (charter §6.3)— y se trata como valor:
    verificar que exista en disco es responsabilidad de la ingesta, no del dominio.
    ``content_hash`` es un identificador opaco no vacío; su algoritmo y formato
    los fija HU-006.
    """

    media_type: MediaType
    width: int
    height: int
    content_hash: str
    source: Path

    def __post_init__(self) -> None:
        if self.width < 1:
            msg = f"width debe ser >= 1 px, se recibió {self.width}"
            raise ValueError(msg)
        if self.height < 1:
            msg = f"height debe ser >= 1 px, se recibió {self.height}"
            raise ValueError(msg)
        if not self.content_hash.strip():
            msg = "content_hash no puede estar vacío"
            raise ValueError(msg)

    @property
    def orientation(self) -> Orientation:
        """Orientación derivada: alto > ancho ⇒ V · ancho > alto ⇒ H · iguales ⇒ SQUARE."""
        if self.height > self.width:
            return Orientation.VERTICAL
        if self.width > self.height:
            return Orientation.HORIZONTAL
        return Orientation.SQUARE
