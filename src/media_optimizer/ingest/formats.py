"""Identificación del formato de imagen por su firma binaria.

En simple: mira los primeros bytes del archivo para saber qué es de verdad, sin
creerle a la extensión del nombre. Distingue tres situaciones: lo que sabemos
procesar (JPEG, PNG, WebP), lo que reconocemos pero no podemos abrir (HEIC de
iPhone, AVIF) y lo que no es una imagen. Nunca decodifica la foto: una firma
válida dice qué formato es, no que la imagen esté sana.
"""

from enum import StrEnum
from pathlib import Path

from media_optimizer.core import CorruptMediaError
from media_optimizer.ingest import filesystem

_HEADER_BYTES = 16


class ImageFormat(StrEnum):
    """Formatos de imagen que el sistema sabe identificar."""

    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    HEIC = "heic"
    AVIF = "avif"


SUPPORTED_FORMATS: frozenset[ImageFormat] = frozenset(
    {ImageFormat.JPEG, ImageFormat.PNG, ImageFormat.WEBP}
)
"""Formatos que el stack de visión instalado puede abrir (HEIC y AVIF no lo son)."""

_PREFIX_SIGNATURES: tuple[tuple[ImageFormat, bytes], ...] = (
    (ImageFormat.JPEG, b"\xff\xd8\xff"),
    (ImageFormat.PNG, b"\x89PNG\r\n\x1a\n"),
)

_ISOBMFF_BRANDS: dict[bytes, ImageFormat] = {
    b"heic": ImageFormat.HEIC,
    b"heix": ImageFormat.HEIC,
    b"hevc": ImageFormat.HEIC,
    b"mif1": ImageFormat.HEIC,
    b"msf1": ImageFormat.HEIC,
    b"avif": ImageFormat.AVIF,
    b"avis": ImageFormat.AVIF,
}


def detect_image_format(path: Path) -> ImageFormat | None:
    """Devuelve el formato según la firma del archivo, o ``None`` si no la reconoce.

    Raises:
        CorruptMediaError: si el archivo no se puede leer.
    """
    cabecera = _read_header(path)
    return _match_prefix(cabecera) or _match_riff(cabecera) or _match_isobmff(cabecera)


def is_supported_image(path: Path) -> bool:
    """Indica si el archivo es una imagen que el pipeline puede abrir."""
    return detect_image_format(path) in SUPPORTED_FORMATS


def _read_header(path: Path) -> bytes:
    try:
        return filesystem.read_bytes(path, count=_HEADER_BYTES)
    except OSError as error:
        raise CorruptMediaError(path, f"no se pudo leer el archivo ({error.strerror})") from error


def _match_prefix(header: bytes) -> ImageFormat | None:
    for formato, firma in _PREFIX_SIGNATURES:
        if header.startswith(firma):
            return formato
    return None


def _match_riff(header: bytes) -> ImageFormat | None:
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return ImageFormat.WEBP
    return None


def _match_isobmff(header: bytes) -> ImageFormat | None:
    if header[4:8] != b"ftyp":
        return None
    return _ISOBMFF_BRANDS.get(header[8:12])
