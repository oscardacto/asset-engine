"""Contrato ``SceneScore``: qué tan buena es una toma, en números.

En simple: la boleta de calificaciones de una escena. Dice qué tan bien expuesta
está y qué tan quieta estaba la cámara, y resume ambas cosas en una nota general
para poder ordenar las tomas y quedarse con las mejores.

La nota general **promedia solo lo que se pudo medir**. Eso no es una comodidad:
la nitidez todavía no tiene una forma acordada de medirse, y cuando la tenga
entrará como un componente más sin que este contrato ni quien lo usa cambien.
"""

from dataclasses import dataclass

_MINIMO = 0.0
_MAXIMO = 1.0


@dataclass(frozen=True, slots=True)
class SceneScore:
    """Calificación de una escena: sus componentes y la nota que los resume."""

    scene_index: int
    exposure: float
    stability: float
    sampled_frames: int

    def __post_init__(self) -> None:
        if self.scene_index < 0:
            msg = f"scene_index debe ser >= 0, se recibió {self.scene_index}"
            raise ValueError(msg)
        if self.sampled_frames < 1:
            msg = f"hay que mirar al menos un cuadro, se recibió {self.sampled_frames}"
            raise ValueError(msg)
        for nombre, valor in (("exposure", self.exposure), ("stability", self.stability)):
            if not _MINIMO <= valor <= _MAXIMO:
                msg = f"{nombre} debe estar entre 0 y 1, se recibió {valor}"
                raise ValueError(msg)

    @property
    def components(self) -> tuple[float, ...]:
        """Los componentes que sí se midieron, en orden estable."""
        return (self.exposure, self.stability)

    @property
    def overall(self) -> float:
        """Nota general: la media de los componentes disponibles."""
        medidos = self.components
        return round(sum(medidos) / len(medidos), 4)
