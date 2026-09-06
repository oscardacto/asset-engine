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

from scenedetect import ContentDetector, SceneManager, open_video
from scenedetect.video_stream import VideoOpenFailure

from media_optimizer.core import CorruptMediaError, Scene
from media_optimizer.ingest import filesystem

UMBRAL_POR_DEFECTO = 27.0

_PRIMERA_ESCENA = 0


@dataclass(frozen=True, slots=True)
class PySceneDetectAdapter:
    """Detecta escenas con la librería externa y las devuelve como datos propios."""

    threshold: float = UMBRAL_POR_DEFECTO

    def detect(self, video: Path, *, threshold: float = UMBRAL_POR_DEFECTO) -> tuple[Scene, ...]:
        """Escenas del clip, en orden y sin solaparse.

        Un clip sin cortes devuelve **una** escena que lo cubre entero, no cero:
        que no haya cortes no significa que no haya material.

        Raises:
            CorruptMediaError: si el clip no se puede leer o decodificar.
        """
        ruta = filesystem.system_path(video)
        try:
            flujo = open_video(ruta)
            gestor = SceneManager()
            gestor.add_detector(ContentDetector(threshold=threshold))
            gestor.detect_scenes(flujo)
            cortes = gestor.get_scene_list()
            duracion = float(flujo.duration.seconds)
        except (OSError, VideoOpenFailure, ValueError) as error:
            raise CorruptMediaError(video, _causa(error)) from error

        if not cortes:
            return (Scene(index=_PRIMERA_ESCENA, start_seconds=0.0, end_seconds=duracion),)
        return tuple(
            Scene(
                index=posicion,
                start_seconds=float(inicio.seconds),
                end_seconds=float(fin.seconds),
            )
            for posicion, (inicio, fin) in enumerate(cortes)
        )


def _causa(error: Exception) -> str:
    """La primera línea del error, que es la que dice qué pasó."""
    primera = str(error).splitlines()
    return primera[0].strip() if primera else "el clip no se pudo abrir"
