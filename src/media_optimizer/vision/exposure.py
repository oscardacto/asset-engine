"""Métricas de exposición: qué tan clara u oscura quedó una foto, en números.

En simple: son las tres medidas que el dueño del negocio ya calculaba a ojo en su
auditoría manual — qué tan brillante es la foto en promedio, cuánta parte se
hundió en negro sin detalle, y cuánta se quemó en blanco puro. Aquí salen de
contar píxeles, así que dos personas (o dos ejecuciones) obtienen exactamente el
mismo número.

El brillo se mide como **luminancia perceptual**: el ojo no pesa igual los tres
colores —el verde aporta mucho más que el azul—, y la auditoría del cliente se
hizo mirando las fotos, no sus canales. Promediar R, G y B daría otro número y
rompería la paridad con esa auditoría. Los umbrales de "negro" y "quemado" llegan
como parámetros: qué tan estricto ser es criterio del negocio, no de este módulo.
"""

from pathlib import Path

import cv2
import numpy as np

from media_optimizer.core import CorruptMediaError
from media_optimizer.ingest import filesystem

Image = np.ndarray

_NIVEL_MAXIMO = 255
_DIMENSIONES_SIN_COLOR = 2  # alto y ancho, sin canal de color
# Rec. 601: cuánto aporta cada color a la luminosidad percibida. OpenCV entrega
# los canales en orden B, G, R — por eso el azul va primero.
_PESOS_BGR = np.array([0.114, 0.587, 0.299], dtype=np.float64)


def decode_image(path: Path) -> Image:
    """Decodifica una imagen leyéndola a través de la capa de acceso al disco.

    Nunca se le da la ruta a OpenCV directamente: su lector no entiende las rutas
    que la capa sí rescata. Se leen los bytes y se decodifican en memoria.

    Raises:
        CorruptMediaError: si el contenido no se puede decodificar.
    """
    crudo = np.frombuffer(filesystem.read_bytes(path), dtype=np.uint8)
    imagen = cv2.imdecode(crudo, cv2.IMREAD_COLOR)
    if imagen is None:
        raise CorruptMediaError(path, "el decodificador no pudo abrir la imagen")
    return imagen


def luminance(image: Image) -> Image:
    """Mapa de luminosidad percibida [0, 255] de una imagen BGR o en grises."""
    if image.ndim == _DIMENSIONES_SIN_COLOR:
        return image.astype(np.float64)
    return image.astype(np.float64) @ _PESOS_BGR


def mean_brightness(image: Image) -> float:
    """Brillo medio de la foto [0, 255], como lo estimaría un ojo humano."""
    return float(luminance(image).mean())


def crushed_shadows_ratio(image: Image, threshold: float) -> float:
    """Fracción de píxeles hundidos en negro: luminosidad estrictamente bajo el umbral."""
    _validar_umbral(threshold)
    mapa = luminance(image)
    return float((mapa < threshold).mean())


def blown_highlights_ratio(image: Image, threshold: float) -> float:
    """Fracción de píxeles quemados en blanco: luminosidad estrictamente sobre el umbral."""
    _validar_umbral(threshold)
    mapa = luminance(image)
    return float((mapa > threshold).mean())


def _validar_umbral(threshold: float) -> None:
    if not 0 <= threshold <= _NIVEL_MAXIMO:
        msg = f"el umbral debe estar en [0, {_NIVEL_MAXIMO}], se recibió {threshold!r}"
        raise ValueError(msg)
