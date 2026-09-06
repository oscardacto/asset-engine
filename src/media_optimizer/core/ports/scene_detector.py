"""El puerto de detección de escenas: qué se le pide, sin decir quién lo hace.

En simple: el dominio necesita saber en qué tramos se parte un clip, pero no
tiene por qué saber con qué herramienta se averigua. Aquí se describe solo la
pregunta —dame las escenas de este clip, con esta sensibilidad— y la respuesta,
que son datos propios del proyecto.

Gracias a eso, quien orquesta el pipeline puede pedir escenas sin importar nada
de la librería que las detecta, y las pruebas pueden responder con escenas
inventadas sin abrir un solo video.
"""

from pathlib import Path
from typing import Protocol

from media_optimizer.core.scene import Scene


class SceneDetectorPort(Protocol):
    """Lo que el dominio espera de cualquier detector de escenas."""

    def detect(self, video: Path, *, threshold: float) -> tuple[Scene, ...]:
        """Escenas del clip, en orden y sin solaparse.

        ``threshold`` es cuánto tiene que cambiar la imagen para considerar que
        hubo un corte: más bajo, más sensible.

        Raises:
            CorruptMediaError: si el clip no se puede leer o decodificar.
        """
        ...
