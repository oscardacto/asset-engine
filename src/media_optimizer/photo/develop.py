"""Motor de revelado: transformaciones componibles que el perfil ordena como datos.

En simple: revelar una foto es aplicarle una secuencia de retoques —contraste,
calidez, saturación— y aquí vive el motor que los aplica en orden. Qué retoques,
con qué valores y en qué orden **no se decide aquí**: llega del perfil de negocio
como datos. Agregar un retoque nuevo es registrarlo en la tabla del final; el
motor no cambia.

Cada aplicación queda anotada en el historial de transformaciones — la evidencia
auditable de cómo se llegó del original a la salida. La foto de entrada jamás se
muta: cada paso devuelve una imagen nueva.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import cv2
import numpy as np

from media_optimizer.core import (
    InvalidInputError,
    ParamValue,
    Transform,
    TransformHistory,
)
from media_optimizer.vision import Image, luminance

_NIVEL_MAXIMO = 255.0

ApplyFn = Callable[[Image, Mapping[str, ParamValue]], Image]
ValidateFn = Callable[[Mapping[str, ParamValue]], None]


@dataclass(frozen=True, slots=True)
class TransformSpec:
    """El contrato de una transformación: cómo se valida y cómo se aplica."""

    apply: ApplyFn
    validate: ValidateFn


def build_plan(steps: tuple[Transform, ...]) -> tuple[Transform, ...]:
    """Valida el plan completo antes de tocar una sola foto.

    Un nombre desconocido o un parámetro fuera de rango es un dato del usuario
    mal escrito en el perfil: falla aquí, con el nombre del paso, y no a mitad
    de un lote.
    """
    for paso in steps:
        spec = TRANSFORMS.get(paso.name)
        if spec is None:
            disponibles = ", ".join(sorted(TRANSFORMS))
            msg = f"el retoque '{paso.name}' no existe; disponibles: {disponibles}"
            raise InvalidInputError(msg)
        try:
            spec.validate(paso.params)
        except ValueError as error:
            msg = f"parámetros inválidos en '{paso.name}': {error}"
            raise InvalidInputError(msg) from error
    return steps


def apply_pipeline(image: Image, steps: tuple[Transform, ...]) -> tuple[Image, TransformHistory]:
    """Aplica el plan en orden y devuelve la imagen final con su historial."""
    actual = image
    historial = TransformHistory()
    for paso in build_plan(steps):
        actual = TRANSFORMS[paso.name].apply(actual, paso.params)
        historial = historial.append(paso)
    return actual, historial


def _requerir(params: Mapping[str, ParamValue], nombre: str, minimo: float, maximo: float) -> float:
    valor = params.get(nombre)
    if not isinstance(valor, int | float) or isinstance(valor, bool):
        msg = f"falta el parámetro numérico {nombre!r}"
        raise ValueError(msg)
    if not minimo <= float(valor) <= maximo:
        msg = f"{nombre} debe estar en [{minimo}, {maximo}], se recibió {valor!r}"
        raise ValueError(msg)
    return float(valor)


# --- clahe: contraste local sin reventar el color ---------------------------


def _validar_clahe(params: Mapping[str, ParamValue]) -> None:
    _requerir(params, "clip_limit", 0.1, 10.0)
    _requerir(params, "tile_size", 2, 32)


def _aplicar_clahe(image: Image, params: Mapping[str, ParamValue]) -> Image:
    """Ecualiza el contraste por zonas sobre la luminosidad, sin tocar el color."""
    clip = _requerir(params, "clip_limit", 0.1, 10.0)
    tile = int(_requerir(params, "tile_size", 2, 32))
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    ecualizador = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tile, tile))
    lab[:, :, 0] = ecualizador.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


# --- white_balance: calidez solo en luces (referencia: revelado 25-jul) -----


def _validar_wb(params: Mapping[str, ParamValue]) -> None:
    _requerir(params, "warmth", -0.2, 0.2)


def _aplicar_wb(image: Image, params: Mapping[str, ParamValue]) -> Image:
    """Calienta (o enfría) la imagen, con más fuerza cuanto más luminosa la zona.

    Es la técnica del revelado de referencia: la calidez entra en las luces —
    donde se ve acogedora— sin ensuciar las sombras.
    """
    calidez = _requerir(params, "warmth", -0.2, 0.2)
    peso = (luminance(image).astype(np.float32) / _NIVEL_MAXIMO)[:, :, np.newaxis]
    flotante = image.astype(np.float32)
    # BGR: la calidez sube el rojo y baja el azul, ponderada por la luz local.
    flotante[:, :, 2] *= 1.0 + calidez * peso[:, :, 0]
    flotante[:, :, 0] *= 1.0 - calidez * peso[:, :, 0]
    return np.clip(flotante, 0, _NIVEL_MAXIMO).astype(np.uint8)


# --- saturation: con el tope que el perfil imponga --------------------------


def _validar_saturation(params: Mapping[str, ParamValue]) -> None:
    factor = _requerir(params, "factor", 0.0, 2.0)
    tope = _requerir(params, "max_factor", 1.0, 2.0)
    if factor > tope:
        msg = f"factor {factor} excede el tope del perfil {tope}"
        raise ValueError(msg)


def _aplicar_saturation(image: Image, params: Mapping[str, ParamValue]) -> Image:
    """Multiplica la saturación, dentro del tope que el negocio fijó."""
    factor = _requerir(params, "factor", 0.0, 2.0)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, _NIVEL_MAXIMO)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


TRANSFORMS: dict[str, TransformSpec] = {
    "clahe": TransformSpec(apply=_aplicar_clahe, validate=_validar_clahe),
    "white_balance": TransformSpec(apply=_aplicar_wb, validate=_validar_wb),
    "saturation": TransformSpec(apply=_aplicar_saturation, validate=_validar_saturation),
}
