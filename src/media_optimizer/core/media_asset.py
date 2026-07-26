"""Contrato ``MediaAsset``: la ficha técnica inmutable de una foto o un video.

En simple: cada archivo de medio se representa con una tarjeta que dice qué es
(foto/video), cuánto mide, cuál es su huella de contenido y de dónde salió.
La tarjeta no se puede alterar después de creada y nunca abre el archivo real.
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
    """Ficha inmutable de un medio: tipo, dimensiones en px, hash de contenido y origen.

    ``source`` es la ruta del archivo original como dato — aquí nunca se lee el
    disco ni se modifica el original. ``content_hash`` es una huella opaca ya
    calculada por quien construye la ficha. Valores imposibles (dimensiones < 1,
    hash vacío) fallan de inmediato con ``ValueError``.
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
        """Más alto que ancho ⇒ vertical · más ancho ⇒ horizontal · iguales ⇒ cuadrada."""
        if self.height > self.width:
            return Orientation.VERTICAL
        if self.width > self.height:
            return Orientation.HORIZONTAL
        return Orientation.SQUARE
