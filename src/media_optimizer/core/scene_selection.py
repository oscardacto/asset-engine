"""Decide qué escenas sirven y, sobre todo, explica por qué las otras no.

En simple: mira cada toma y dice si vale la pena usarla. Cuando no, dice **qué
falló** — que quedó muy corta, que la cámara se movía, que la luz no daba. Esa
explicación es el verdadero producto: un descarte a secas dice que el clip no
sirve; con la causa, dice qué grabar mejor la próxima vez.

Por eso se reportan **todas** las causas y no la primera que aparece: una toma
corta y temblorosa tiene dos cosas que corregir, no una.

**Los límites se miran componente por componente, nunca sobre la nota general.**
Esa nota promedia lo que se pudo medir, así que el día que se sume una métrica
nueva cambiaría de valor sola — y con ella, en silencio, qué se descarta. Mirar
cada componente por su lado deja el criterio estable ante ese cambio.
"""

from dataclasses import dataclass
from enum import StrEnum

from media_optimizer.core.scene import Scene
from media_optimizer.core.scene_score import SceneScore

_MINIMO = 0.0
_MAXIMO = 1.0


class DiscardReason(StrEnum):
    """Por qué una escena no sirve. El valor es lo que se muestra al usuario."""

    POOR_EXPOSURE = "poor_exposure"
    TOO_SHORT = "too_short"
    UNSTABLE = "unstable"


@dataclass(frozen=True, slots=True)
class SceneThresholds:
    """Lo mínimo que una escena tiene que cumplir, según el criterio del negocio."""

    min_duration_seconds: float
    min_exposure: float
    min_stability: float

    def __post_init__(self) -> None:
        if self.min_duration_seconds <= _MINIMO:
            msg = (
                "min_duration_seconds debe ser mayor que cero, "
                f"se recibió {self.min_duration_seconds}"
            )
            raise ValueError(msg)
        for nombre, valor in (
            ("min_exposure", self.min_exposure),
            ("min_stability", self.min_stability),
        ):
            if not _MINIMO <= valor <= _MAXIMO:
                msg = f"{nombre} debe estar entre 0 y 1, se recibió {valor}"
                raise ValueError(msg)


# Punto de partida derivado de medir 19 escenas de material real del cliente, no
# elegido a ojo: la estabilidad de un celular a pulso llega como mucho a 0.4, así
# que un mínimo de 0.5 dejaría el lote vacío. La exposición de ese material va de
# 0.8 a 0.98, de modo que nada se descarta hoy por luz. Y las tomas de menos de
# segundo y medio suelen ser el barrido entre planos, no un plano.
UMBRALES_POR_DEFECTO = SceneThresholds(
    min_duration_seconds=1.5,
    min_exposure=0.6,
    min_stability=0.15,
)


@dataclass(frozen=True, slots=True)
class SceneVerdict:
    """Qué se decidió sobre una escena, y por qué."""

    scene_index: int
    reasons: tuple[DiscardReason, ...]

    @property
    def keep(self) -> bool:
        """Se conserva si no hay ninguna causa de descarte.

        Se deduce de las causas en vez de guardarse aparte: así no puede existir
        una escena marcada como buena que además traiga motivos para descartarla.
        """
        return not self.reasons


def judge_scene(scene: Scene, score: SceneScore, thresholds: SceneThresholds) -> SceneVerdict:
    """Juzga una escena y devuelve todas las causas por las que no serviría."""
    causas: list[DiscardReason] = []
    if scene.duration_seconds < thresholds.min_duration_seconds:
        causas.append(DiscardReason.TOO_SHORT)
    if score.exposure < thresholds.min_exposure:
        causas.append(DiscardReason.POOR_EXPOSURE)
    if score.stability < thresholds.min_stability:
        causas.append(DiscardReason.UNSTABLE)
    return SceneVerdict(
        scene_index=scene.index,
        reasons=tuple(sorted(causas, key=lambda causa: causa.value)),
    )


def select_scenes(
    scenes: tuple[Scene, ...],
    scores: tuple[SceneScore, ...],
    thresholds: SceneThresholds,
) -> tuple[SceneVerdict, ...]:
    """Juzga todas las escenas de un clip, en su orden.

    Que se descarten todas es un resultado válido: significa que hay que volver a
    grabar, no que el programa falló.

    Raises:
        ValueError: si no hay una calificación por escena.
    """
    if len(scenes) != len(scores):
        msg = (
            "hace falta la misma cantidad de escenas y de calificaciones: "
            f"{len(scenes)} y {len(scores)}"
        )
        raise ValueError(msg)
    return tuple(
        judge_scene(escena, nota, thresholds) for escena, nota in zip(scenes, scores, strict=True)
    )


def kept_scenes(
    scenes: tuple[Scene, ...],
    scores: tuple[SceneScore, ...],
    thresholds: SceneThresholds,
) -> tuple[Scene, ...]:
    """Solo las escenas que sobreviven al descarte, en su orden original."""
    veredictos = select_scenes(scenes, scores, thresholds)
    return tuple(
        escena for escena, veredicto in zip(scenes, veredictos, strict=True) if veredicto.keep
    )
