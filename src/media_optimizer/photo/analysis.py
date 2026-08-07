"""Score de exposición y veredicto técnico: de los números medidos a una decisión.

En simple: ya medimos qué tan brillante quedó la foto y cuánto se hundió en negro
o se quemó en blanco. Aquí esos números se convierten en una calificación de 0 a 1
y en un veredicto — publicable, de apoyo, o descartar — siempre con sus causas,
para que nadie tenga que adivinar por qué una foto quedó fuera.

La calificación castiga la **distancia al objetivo**, no premia el brillo: una foto
más clara que el objetivo del negocio está tan mal como una más oscura, y una
quemada está peor. Todos los objetivos, pesos y cortes llegan del perfil de
negocio: este módulo no sabe qué es "hospedaje", sabe restar.
"""

import math
from dataclasses import dataclass

from media_optimizer.core import Verdict

_NIVEL_MAXIMO = 255.0
_FLAG_WHATSAPP = "whatsapp_compressed"


@dataclass(frozen=True, slots=True)
class ExposureThresholds:
    """Los criterios de exposición de un negocio, como datos.

    Los poblará la carga del perfil; mientras tanto, quien invoque los construye.
    """

    brightness_target: float
    crushed_shadows_weight: float
    blown_highlights_weight: float
    publishable_min_score: float
    support_min_score: float

    def __post_init__(self) -> None:
        if not 0 <= self.brightness_target <= _NIVEL_MAXIMO:
            msg = f"brightness_target debe estar en [0, 255], se recibió {self.brightness_target!r}"
            raise ValueError(msg)
        for nombre in ("crushed_shadows_weight", "blown_highlights_weight"):
            valor = getattr(self, nombre)
            if not math.isfinite(valor) or valor < 0:
                msg = f"{nombre} debe ser finito y >= 0, se recibió {valor!r}"
                raise ValueError(msg)
        if not 0 <= self.support_min_score <= self.publishable_min_score <= 1:
            msg = (
                "los cortes deben cumplir 0 <= support_min_score <= publishable_min_score <= 1, "
                f"se recibió {self.support_min_score!r} y {self.publishable_min_score!r}"
            )
            raise ValueError(msg)


def exposure_score(
    brightness: float,
    crushed_ratio: float,
    blown_ratio: float,
    thresholds: ExposureThresholds,
) -> float:
    """Calificación de exposición [0, 1]: 1 es el objetivo del negocio, exacto y limpio.

    Parte de qué tan lejos quedó el brillo del objetivo y resta las zonas
    hundidas y quemadas según el peso que el negocio les dé.
    """
    distancia = abs(brightness - thresholds.brightness_target) / _NIVEL_MAXIMO
    castigo = (
        crushed_ratio * thresholds.crushed_shadows_weight
        + blown_ratio * thresholds.blown_highlights_weight
    )
    return max(0.0, min(1.0, 1.0 - distancia - castigo))


def verdict_for(
    score: float,
    flags: tuple[str, ...],
    thresholds: ExposureThresholds,
) -> tuple[Verdict, tuple[str, ...]]:
    """El destino técnico de la foto y las causas que lo explican.

    El material que pasó por WhatsApp nunca es publicable — ya perdió calidad de
    forma irrecuperable — pero puede servir de apoyo si lo demás está bien.
    """
    causas: list[str] = []
    veredicto = _por_score(score, thresholds, causas)
    if _FLAG_WHATSAPP in flags and veredicto is Verdict.PUBLISHABLE:
        veredicto = Verdict.SUPPORT
        causas.append("comprimida por WhatsApp: la calidad perdida no se recupera")
    return veredicto, tuple(causas)


def _por_score(score: float, thresholds: ExposureThresholds, causas: list[str]) -> Verdict:
    if score >= thresholds.publishable_min_score:
        return Verdict.PUBLISHABLE
    if score >= thresholds.support_min_score:
        causas.append(
            f"exposición {score:.2f} bajo el corte publicable {thresholds.publishable_min_score}"
        )
        return Verdict.SUPPORT
    causas.append(f"exposición {score:.2f} bajo el corte de apoyo {thresholds.support_min_score}")
    return Verdict.DISCARD
