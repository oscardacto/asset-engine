"""Generador de imágenes sintéticas para pruebas: exposición, orientación y corrupción.

En simple: fabrica fotos de mentira con propiedades exactas — "una imagen de
brillo 40", "una vertical 1080x1920", "un JPEG roto a la mitad" — para que los
tests nunca necesiten fotos reales del cliente. Misma semilla ⇒ mismos bytes.
"""

from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from media_optimizer.ingest import filesystem

Image = NDArray[np.uint8]

_MAX_LEVEL = 255
_MIN_QUALITY, _MAX_QUALITY = 1, 100
_TIFF_HEADER_SIZE = 8
_IFD_ENTRY_SIZE = 12
_TAG_ORIENTATION = 0x0112
_TAG_EXIF_POINTER = 0x8769
_TAG_DATETIME_ORIGINAL = 0x9003


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
    filesystem.write_bytes(path, encode_jpeg(image, quality=quality))
    return path


def truncated_jpeg(image: Image, keep_fraction: float = 0.5) -> bytes:
    """JPEG cortado a mitad de stream: simula un archivo a medio copiar."""
    if not 0 < keep_fraction < 1:
        msg = f"keep_fraction debe estar en (0, 1), se recibió {keep_fraction}"
        raise ValueError(msg)
    completo = encode_jpeg(image)
    return completo[: max(1, int(len(completo) * keep_fraction))]


def jpeg_with_exif(image: Image, exif: bytes, quality: int = 90) -> bytes:
    """JPEG con un bloque EXIF insertado tal cual, incluso si está corrupto.

    En simple: pega los metadatos que se le den —válidos o rotos a propósito—
    justo después de la cabecera, para poder probar cómo reacciona el lector.
    """
    completo = encode_jpeg(image, quality=quality)
    cuerpo = b"Exif\x00\x00" + exif
    segmento = b"\xff\xe1" + (len(cuerpo) + 2).to_bytes(2, "big") + cuerpo
    return completo[:2] + segmento + completo[2:]


def exif_block(orientation: int | None = None, captured_at: str | None = None) -> bytes:
    """Bloque EXIF mínimo y válido con las etiquetas que se pidan."""
    entradas: list[tuple[int, int, int, bytes]] = []
    extra = b""
    offset_extra = _TIFF_HEADER_SIZE + 2 + _IFD_ENTRY_SIZE * _count(orientation, captured_at) + 4

    if orientation is not None:
        entradas.append((_TAG_ORIENTATION, 3, 1, orientation.to_bytes(2, "little") + b"\x00\x00"))
    if captured_at is not None:
        sub_offset = offset_extra
        entradas.append((_TAG_EXIF_POINTER, 4, 1, sub_offset.to_bytes(4, "little")))
        texto = captured_at.encode("ascii") + b"\x00"
        texto_offset = sub_offset + 2 + _IFD_ENTRY_SIZE + 4
        sub = (
            (1).to_bytes(2, "little")
            + _entry(_TAG_DATETIME_ORIGINAL, 2, len(texto), texto_offset.to_bytes(4, "little"))
            + b"\x00\x00\x00\x00"
        )
        extra = sub + texto

    cuerpo = (len(entradas)).to_bytes(2, "little")
    for etiqueta, tipo, cuenta, valor in entradas:
        cuerpo += _entry(etiqueta, tipo, cuenta, valor)
    cuerpo += b"\x00\x00\x00\x00"
    return b"II\x2a\x00" + (_TIFF_HEADER_SIZE).to_bytes(4, "little") + cuerpo + extra


def _count(orientation: int | None, captured_at: str | None) -> int:
    return (orientation is not None) + (captured_at is not None)


def _entry(tag: int, kind: int, count: int, value: bytes) -> bytes:
    return (
        tag.to_bytes(2, "little") + kind.to_bytes(2, "little") + count.to_bytes(4, "little") + value
    )


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
