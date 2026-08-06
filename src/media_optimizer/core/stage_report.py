"""Contrato ``StageReport``: qué entrega cada etapa del pipeline al terminar.

En simple: cuando una etapa acaba —leer la carpeta, analizar las fotos, revelarlas—
deja una ficha que dice cuánto tardó, cuánta memoria llegó a usar, qué le hizo a
las imágenes y qué notas les puso. Sin esa ficha no hay forma de saber por qué el
programa fue lento o de auditar cómo llegó a un resultado.

Hay una trampa en esa ficha. El programa promete que **la misma entrada produce
siempre la misma salida**, y hay pruebas que lo comprueban comparando resultados
byte a byte. Pero el tiempo y la memoria cambian en cada ejecución: si uno de esos
números entrara en una comparación así, la prueba fallaría de vez en cuando y el
error parecería un fantasma —"0.031 contra 0.029"— en lugar de un defecto de
diseño. Por eso lo comparable vive en un tipo aparte, ``ReproducibleStageSummary``:
lo que se compara no *puede* traer un tiempo dentro, porque no encaja.

Aquí no se mide nada. Medir es impuro y le toca a la capa que orquesta las etapas;
este módulo solo recibe lo ya medido y lo guarda bien.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from media_optimizer.core.transform import TransformHistory

_MINIMO = 0


@dataclass(frozen=True, slots=True)
class ReproducibleStageSummary:
    """La parte de un reporte que dos ejecuciones iguales producen idéntica.

    Es lo único que puede compararse en una prueba de reproducibilidad o entrar en
    un manifiesto que se firma por contenido.
    """

    stage: str
    transforms: TransformHistory
    scores: Mapping[str, float] = field(hash=False)


@dataclass(frozen=True, slots=True)
class StageReport:
    """Ficha de una etapa: cuánto tardó, cuánta memoria usó, qué hizo y qué puntuó.

    ``duration_seconds`` y ``peak_memory_bytes`` los mide quien ejecuta la etapa y
    cambian entre corridas; el resto es reproducible. Para comparar dos corridas se
    usa ``reproducible_part()``, no el reporte entero.

    Un tiempo o una memoria negativos no son un dato pobre sino imposible, así que
    fallan al construir en vez de propagarse hasta un informe.
    """

    stage: str
    duration_seconds: float
    peak_memory_bytes: int
    transforms: TransformHistory = field(default_factory=TransformHistory)
    scores: Mapping[str, float] = field(default_factory=dict, hash=False)

    def __post_init__(self) -> None:
        if not self.stage.strip():
            msg = "toda etapa necesita un nombre no vacío"
            raise ValueError(msg)
        if not math.isfinite(self.duration_seconds) or self.duration_seconds < _MINIMO:
            msg = (
                "duration_seconds debe ser un número finito >= 0, "
                f"se recibió {self.duration_seconds!r}"
            )
            raise ValueError(msg)
        if self.peak_memory_bytes < _MINIMO:
            msg = f"peak_memory_bytes debe ser >= 0, se recibió {self.peak_memory_bytes!r}"
            raise ValueError(msg)
        object.__setattr__(self, "scores", _scores_ordenados(self.scores, self.stage))

    def reproducible_part(self) -> ReproducibleStageSummary:
        """Lo que dos corridas idénticas producen igual: sin tiempo ni memoria."""
        return ReproducibleStageSummary(
            stage=self.stage, transforms=self.transforms, scores=self.scores
        )


def _scores_ordenados(scores: Mapping[str, float], stage: str) -> Mapping[str, float]:
    normalizados: dict[str, float] = {}
    for nombre, valor in sorted(scores.items()):
        if not nombre.strip():
            msg = f"la etapa {stage!r} tiene un score sin nombre"
            raise ValueError(msg)
        if not math.isfinite(valor):
            msg = f"el score {nombre!r} de {stage!r} debe ser finito, se recibió {valor!r}"
            raise ValueError(msg)
        normalizados[nombre] = valor
    return MappingProxyType(normalizados)
