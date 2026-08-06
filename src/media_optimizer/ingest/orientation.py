"""Orientación real de una foto: vertical, horizontal o cuadrada.

En simple: parece trivial —basta comparar ancho y alto— pero no lo es. Los
móviles guardan la foto tal como salió del sensor y anotan aparte "esto va
girado"; al abrirla, el visor la endereza. Así que la misma foto puede medir
vertical en el archivo y verse horizontal en pantalla.

Aquí se decide cuál manda: **la que se ve**. Es la que anotó el cliente al
revisar su archivo y la que importa para decidir si una foto sirve para una
story. La medida cruda se conserva al lado, para poder explicar la diferencia
cuando alguien la note.
"""

from dataclasses import dataclass

from media_optimizer.core import Orientation
from media_optimizer.ingest.dimensions import ImageSize
from media_optimizer.ingest.exif import ExifOrientation, oriented_size


@dataclass(frozen=True, slots=True)
class AssetOrientation:
    """Orientación de un asset, antes y después de aplicar el giro declarado."""

    raw: Orientation
    effective: Orientation

    @property
    def rotated(self) -> bool:
        """Indica si el archivo se ve distinto de como está guardado."""
        return self.raw is not self.effective


def detect_orientation(
    size: ImageSize, exif_orientation: ExifOrientation | None = None
) -> AssetOrientation:
    """Devuelve la orientación cruda y la que se verá al abrir la imagen."""
    return AssetOrientation(
        raw=_clasificar(size),
        effective=_clasificar(oriented_size(size, exif_orientation)),
    )


def _clasificar(size: ImageSize) -> Orientation:
    if size.height > size.width:
        return Orientation.VERTICAL
    if size.width > size.height:
        return Orientation.HORIZONTAL
    return Orientation.SQUARE
