"""Contrato ``Scene``: un tramo continuo de video entre dos cortes.

En simple: un clip grabado de corrido suele contener varias tomas — la cámara
entra, se detiene, gira. Cada una de esas partes es una escena, y aquí se
describe con dónde empieza, dónde acaba y a qué clip pertenece.

Es un dato, no un video: no guarda imágenes ni sabe leer archivos. Eso permite
razonar sobre las escenas, ordenarlas y descartarlas sin abrir nada, y sobre todo
que ninguna estructura de la librería que las detecta se filtre al dominio.
"""

from dataclasses import dataclass

_MINIMO = 0.0


@dataclass(frozen=True, slots=True)
class Scene:
    """Un tramo de video entre dos cortes, medido en segundos desde el inicio."""

    index: int
    start_seconds: float
    end_seconds: float

    def __post_init__(self) -> None:
        if self.index < 0:
            msg = f"index debe ser >= 0, se recibió {self.index}"
            raise ValueError(msg)
        if self.start_seconds < _MINIMO:
            msg = f"start_seconds debe ser >= 0, se recibió {self.start_seconds}"
            raise ValueError(msg)
        if self.end_seconds <= self.start_seconds:
            msg = (
                f"la escena {self.index} termina antes de empezar: "
                f"{self.end_seconds} <= {self.start_seconds}"
            )
            raise ValueError(msg)

    @property
    def duration_seconds(self) -> float:
        """Cuánto dura la escena."""
        return round(self.end_seconds - self.start_seconds, 3)
