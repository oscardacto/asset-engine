"""Generador de imágenes sintéticas para pruebas: exposición, orientación y corrupción.

En simple: fabrica fotos de mentira con propiedades exactas — "una imagen de
brillo 40", "una vertical 1080x1920", "un JPEG roto a la mitad" — para que los
tests nunca necesiten fotos reales del cliente. Misma semilla ⇒ mismos bytes.
"""

from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

Image = NDArray[np.uint8]

_MAX_LEVEL = 255
_MIN_QUALITY, _MAX_QUALITY = 1, 100


def flat_image(width: int, height: int, brightness: int) -> Image:
    """Imagen de un solo tono: su brillo medio es exactamente ``brightness``."""
    _validate_dimensions(width, height)
    if not 0 <= brightness <= _MAX_LEVEL:
        msg = f"brightness debe estar en [0, {_MAX_LEVEL}], se recibió {brightness}"
        raise ValueError(msg)
    return np.full((height, width, 3), brightness, dtype=np.uint8)


def textured_image(
    width: int, height: int, mean_brightness: int, seed: int, spread: int = 20
) -> Image:
    """Imagen con textura aleatoria reproducible y brillo medio ≈ ``mean_brightness``.

    La media real queda a ±2 del objetivo cuando este está en [30, 225]; fuera de
    ese rango el recorte a [0, 255] la desplaza (para extremos exactos usar
    :func:`flat_image`).
    """
    _validate_dimensions(width, height)
    if not 0 <= mean_brightness <= _MAX_LEVEL:
        msg = f"mean_brightness debe estar en [0, {_MAX_LEVEL}], se recibió {mean_brightness}"
        raise ValueError(msg)
    rng = np.random.default_rng(seed)
    ruido = rng.normal(loc=mean_brightness, scale=spread, size=(height, width, 3))
    return np.clip(ruido, 0, 255).astype(np.uint8)


def encode_jpeg(image: Image, quality: int = 90) -> bytes:
    """Codifica la imagen a bytes JPEG con la calidad dada."""
    if not _MIN_QUALITY <= quality <= _MAX_QUALITY:
        msg = f"quality debe estar en [{_MIN_QUALITY}, {_MAX_QUALITY}], se recibió {quality}"
        raise ValueError(msg)
    ok, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:  # pragma: no cover - cv2 no falla con arrays uint8 válidos
        msg = "cv2 no pudo codificar la imagen a JPEG"
        raise ValueError(msg)
    return buffer.tobytes()


def write_jpeg(path: Path, image: Image, quality: int = 90) -> Path:
    """Escribe la imagen como archivo JPEG y devuelve la misma ruta."""
    path.write_bytes(encode_jpeg(image, quality=quality))
    return path


def truncated_jpeg(image: Image, keep_fraction: float = 0.5) -> bytes:
    """JPEG cortado a mitad de stream: simula un archivo a medio copiar."""
    if not 0 < keep_fraction < 1:
        msg = f"keep_fraction debe estar en (0, 1), se recibió {keep_fraction}"
        raise ValueError(msg)
    completo = encode_jpeg(image)
    return completo[: max(1, int(len(completo) * keep_fraction))]


def not_an_image(size: int = 256) -> bytes:
    """Bytes deterministas que ningún decodificador de imagen reconoce."""
    if size < 1:
        msg = f"size debe ser >= 1, se recibió {size}"
        raise ValueError(msg)
    patron = b"NO-IMAGEN-"
    return (patron * (size // len(patron) + 1))[:size]


def _validate_dimensions(width: int, height: int) -> None:
    if width < 1 or height < 1:
        msg = f"las dimensiones deben ser >= 1 px, se recibió {width}x{height}"
        raise ValueError(msg)
