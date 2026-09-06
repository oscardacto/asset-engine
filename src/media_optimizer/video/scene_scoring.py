"""Puntúa cada escena de un clip mirando unos pocos cuadros repartidos.

En simple: para saber si una toma sirve no hace falta ver el clip entero. Se
salta a unos pocos momentos repartidos por la escena, se miran esos cuadros y se
califica con ellos.

**No se recorre el video.** El charter prohíbe cargar un clip completo en memoria,
así que en vez de leer cuadro por cuadro se salta directamente a las posiciones
que interesan. Una escena de treinta segundos cuesta lo mismo que una de tres.

Si un cuadro no se puede leer se salta y se sigue con los demás: una escena se
califica con lo que haya. Solo cuando no se puede leer ninguno se aparta.
"""

from pathlib import Path

import cv2
import numpy as np

from media_optimizer.core import CorruptMediaError, Scene, SceneScore
from media_optimizer.ingest import filesystem
from media_optimizer.photo import ExposureThresholds, exposure_score
from media_optimizer.vision import (
    Image,
    blown_highlights_ratio,
    crushed_shadows_ratio,
    luminance,
    mean_brightness,
)

MUESTRAS_POR_ESCENA = 5

# Cada muestra es un cuadro y el que le sigue, para poder medir el movimiento.
Muestra = tuple["Image", "Image | None"]

# Debajo de este nivel un pixel cuenta como negro hundido; encima del otro, como
# luz quemada. Son los mismos umbrales con los que se analizan las fotos.
UMBRAL_NEGRO = 26.0
UMBRAL_QUEMADO = 250.0

_ESTABILIDAD_PERFECTA = 1.0
# Cuánta diferencia entre dos cuadros seguidos se considera ya "movimiento total".
# Se mide entre cuadros **contiguos**, no entre las muestras: dos muestras separadas
# por un segundo difieren mucho aunque la cámara estuviera perfectamente quieta, y
# medirlo así calificaba de inestable cualquier recorrido normal.
_DIFERENCIA_DE_REFERENCIA = 12.0


def score_scene(
    video: Path,
    scene: Scene,
    thresholds: ExposureThresholds,
    *,
    samples: int = MUESTRAS_POR_ESCENA,
) -> SceneScore:
    """Califica una escena mirando cuadros repartidos por su duración.

    Raises:
        CorruptMediaError: si no se pudo leer ni un solo cuadro de la escena.
    """
    muestras = _muestrear(video, scene, samples)
    if not muestras:
        msg = f"no se pudo leer ningún cuadro de la escena {scene.index}"
        raise CorruptMediaError(video, msg)

    cuadros = [muestra[0] for muestra in muestras]
    exposicion = sum(_exposicion_de(cuadro, thresholds) for cuadro in cuadros) / len(cuadros)
    return SceneScore(
        scene_index=scene.index,
        exposure=round(exposicion, 4),
        stability=_estabilidad_de(muestras),
        sampled_frames=len(cuadros),
    )


def score_scenes(
    video: Path,
    scenes: tuple[Scene, ...],
    thresholds: ExposureThresholds,
    *,
    samples: int = MUESTRAS_POR_ESCENA,
) -> tuple[SceneScore, ...]:
    """Califica todas las escenas de un clip, en su orden."""
    return tuple(score_scene(video, escena, thresholds, samples=samples) for escena in scenes)


def _muestrear(video: Path, scene: Scene, samples: int) -> list[Muestra]:
    """Muestras de la escena: en cada momento, el cuadro y el que le sigue.

    Se lee el cuadro contiguo porque la estabilidad se mide entre cuadros
    seguidos. El siguiente puede faltar al final del clip, y entonces esa muestra
    solo aporta exposición.
    """
    captura = cv2.VideoCapture(filesystem.system_path(video))
    try:
        if not captura.isOpened():
            return []
        muestras: list[Muestra] = []
        for momento in _momentos(scene, samples):
            cuadro = _leer_en(captura, momento)
            if cuadro is None:
                continue
            leido, siguiente = captura.read()
            muestras.append((cuadro, siguiente if leido else None))
        return muestras
    finally:
        captura.release()


def _momentos(scene: Scene, samples: int) -> tuple[float, ...]:
    """Instantes repartidos por la escena, siempre los mismos para la misma escena."""
    cuantos = max(1, samples)
    if cuantos == 1:
        return (scene.start_seconds + scene.duration_seconds / 2,)
    paso = scene.duration_seconds / (cuantos + 1)
    return tuple(scene.start_seconds + paso * (posicion + 1) for posicion in range(cuantos))


def _leer_en(captura: cv2.VideoCapture, segundo: float) -> Image | None:
    """El cuadro en ese instante, o ``None`` si no se pudo leer."""
    captura.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000.0)
    leido, cuadro = captura.read()
    return cuadro if leido and cuadro is not None else None


def _exposicion_de(cuadro: Image, thresholds: ExposureThresholds) -> float:
    return exposure_score(
        mean_brightness(cuadro),
        crushed_shadows_ratio(cuadro, UMBRAL_NEGRO),
        blown_highlights_ratio(cuadro, UMBRAL_QUEMADO),
        thresholds,
    )


def _estabilidad_de(muestras: list[Muestra]) -> float:
    """Qué tan quieta estuvo la cámara: 1 es inmóvil, 0 es cambio total.

    Compara cada cuadro con el inmediatamente siguiente. Si en ningún momento se
    pudo leer el cuadro contiguo no hay movimiento que medir, y no se penaliza lo
    que no se pudo observar.
    """
    diferencias = [
        float(np.abs(luminance(cuadro).astype(np.float32) - luminance(siguiente)).mean())
        for cuadro, siguiente in muestras
        if siguiente is not None
    ]
    if not diferencias:
        return _ESTABILIDAD_PERFECTA
    media = sum(diferencias) / len(diferencias)
    return round(max(0.0, 1.0 - media / _DIFERENCIA_DE_REFERENCIA), 4)
