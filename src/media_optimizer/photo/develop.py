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


# --- shadows: levantar lo oscuro sin lavar lo claro -------------------------


def _validar_shadows(params: Mapping[str, ParamValue]) -> None:
    _requerir(params, "amount", 0.0, 1.0)


def _aplicar_shadows(image: Image, params: Mapping[str, ParamValue]) -> Image:
    """Recupera las sombras con una máscara que pesa lo oscuro y respeta lo claro.

    La ganancia entra al cuadrado de la oscuridad local: mucha en el negro,
    casi nada en los medios, cero en las luces — así el interior oscuro del
    apartamento sube sin que la ventana se lave.
    """
    cantidad = _requerir(params, "amount", 0.0, 1.0)
    oscuridad = 1.0 - (luminance(image).astype(np.float32) / _NIVEL_MAXIMO)
    mascara = (oscuridad * oscuridad)[:, :, np.newaxis]
    flotante = image.astype(np.float32)
    levantada = flotante + cantidad * _NIVEL_MAXIMO * mascara * (flotante / _NIVEL_MAXIMO + 0.1)
    return np.clip(levantada, 0, _NIVEL_MAXIMO).astype(np.uint8)


# --- exposure: hacia el objetivo, protegiendo las altas luces ---------------


def _validar_exposure(params: Mapping[str, ParamValue]) -> None:
    _requerir(params, "target_brightness", 1.0, 254.0)


def _aplicar_exposure(image: Image, params: Mapping[str, ParamValue]) -> Image:
    """Acerca el brillo medio al objetivo del negocio sin quemar lo ya luminoso.

    La ganancia se pondera por cuánta luz falta en cada zona: donde ya hay luz
    casi no entra, así una subida de exposición no revienta la ventana.
    """
    objetivo = _requerir(params, "target_brightness", 1.0, 254.0)
    mapa = luminance(image).astype(np.float32)
    actual = float(mapa.mean())
    if actual <= 0:
        return image.copy()
    ganancia = objetivo / actual
    if ganancia >= 1.0:
        margen = (1.0 - mapa / _NIVEL_MAXIMO)[:, :, np.newaxis]
        factor = 1.0 + (ganancia - 1.0) * margen
    else:
        factor = np.full((*mapa.shape, 1), ganancia, dtype=np.float32)
    salida = image.astype(np.float32) * factor
    return np.clip(salida, 0, _NIVEL_MAXIMO).astype(np.uint8)


# --- crop: recorte centrado al aspecto pedido -------------------------------


def _validar_crop(params: Mapping[str, ParamValue]) -> None:
    _requerir(params, "aspect_width", 1, 32)
    _requerir(params, "aspect_height", 1, 32)


def _aplicar_crop(image: Image, params: Mapping[str, ParamValue]) -> Image:
    """Recorta centrado al aspecto pedido, tocando solo el eje que sobra."""
    aspecto = _requerir(params, "aspect_width", 1, 32) / _requerir(params, "aspect_height", 1, 32)
    alto, ancho = image.shape[:2]
    if ancho / alto > aspecto:
        nuevo_ancho = round(alto * aspecto)
        margen = (ancho - nuevo_ancho) // 2
        return image[:, margen : margen + nuevo_ancho].copy()
    nuevo_alto = round(ancho / aspecto)
    margen = (alto - nuevo_alto) // 2
    return image[margen : margen + nuevo_alto, :].copy()


# --- resize: al nativo de plataforma, con resampling de calidad -------------


def _validar_resize(params: Mapping[str, ParamValue]) -> None:
    _requerir(params, "width", 16, 8192)
    _requerir(params, "height", 16, 8192)


def _aplicar_resize(image: Image, params: Mapping[str, ParamValue]) -> Image:
    """Redimensiona a las medidas exactas con el filtro de reducción fotográfico."""
    ancho = int(_requerir(params, "width", 16, 8192))
    alto = int(_requerir(params, "height", 16, 8192))
    return cv2.resize(image, (ancho, alto), interpolation=cv2.INTER_AREA)


TRANSFORMS["shadows"] = TransformSpec(apply=_aplicar_shadows, validate=_validar_shadows)
TRANSFORMS["exposure"] = TransformSpec(apply=_aplicar_exposure, validate=_validar_exposure)
TRANSFORMS["crop"] = TransformSpec(apply=_aplicar_crop, validate=_validar_crop)
TRANSFORMS["resize"] = TransformSpec(apply=_aplicar_resize, validate=_validar_resize)
