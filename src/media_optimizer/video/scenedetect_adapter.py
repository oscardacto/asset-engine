"""Detector de escenas real: la única parte del proyecto que conoce la librería.

En simple: parte un clip en sus tomas comparando cuánto cambia la imagen entre
cuadros consecutivos. Cuando el cambio supera un umbral, ahí hubo un corte.

Nada de la librería que hace ese trabajo sale de este archivo: entra una ruta y
salen escenas del proyecto. Así, cambiarla por otra —o por un cálculo propio— no
obliga a tocar ni una línea del resto del sistema.

**La ruta se adapta antes de entregarla.** Se midió que la librería no encuentra
un video cuya ruta supera los 260 caracteres si se le pasa tal cual, y sí lo abre
en la forma que el sistema exige. Es el mismo patrón que ya obligó a envolver la
herramienta de video y el manejador de archivos de la biblioteca estándar.
"""

from dataclasses import dataclass
from pathlib import Path

from media_optimizer.core import Scene

UMBRAL_POR_DEFECTO = 27.0


@dataclass(frozen=True, slots=True)
class PySceneDetectAdapter:
    """Detecta escenas con la librería externa y las devuelve como datos propios."""

    threshold: float = UMBRAL_POR_DEFECTO

    def detect(self, video: Path, *, threshold: float = UMBRAL_POR_DEFECTO) -> tuple[Scene, ...]:
        """Escenas del clip, en orden y sin solaparse.

        Raises:
            CorruptMediaError: si el clip no se puede leer o decodificar.
        """
        raise NotImplementedError
