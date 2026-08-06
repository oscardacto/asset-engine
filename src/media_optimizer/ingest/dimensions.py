"""Lectura de las dimensiones declaradas en la cabecera, sin abrir la imagen.

En simple: averigua cuánto mide una foto —y por tanto cuánta memoria pediría al
abrirse— leyendo solo el principio del archivo. Sirve para frenar el archivo
malicioso que dice medir 60.000 x 60.000 antes de que reserve gigabytes, y de
paso da las medidas que el resto del pipeline necesita sin pagar una apertura.

Si un archivo no permite averiguarlas, se devuelve ``None``: nunca se descarta
material por no poder medirlo.
"""

from dataclasses import dataclass
from pathlib import Path

from media_optimizer.ingest import filesystem
from media_optimizer.ingest.formats import ImageFormat

_BYTES_PER_PIXEL = 3
"""OpenCV reserva 3 bytes por píxel al cargar en color (BGR)."""

MAX_DECODED_BYTES = 1024 * 1024 * 1024
"""Techo de memoria estimada al decodificar. Promovible a configuración."""

MAX_SIDE = 65_535
"""Lado máximo admitido, el mayor que el propio formato JPEG puede declarar."""

_HEADER_BYTES = 64 * 1024
_PNG_HEADER_END = 24
_JPEG_MARKER_PREFIX = 0xFF
_JPEG_MIN_SEGMENT_LENGTH = 2
_JPEG_SOF_HEADER_END = 9
_JPEG_SOF_MARKERS = frozenset(
    {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
)
_JPEG_STANDALONE_MARKERS = frozenset({0x01, *range(0xD0, 0xDA)})
_WEBP_MIN_HEADER = 30
_VP8L_MASK = 0x3FFF
_VP8L_HEIGHT_SHIFT = 14
_VP8_START_CODE = b"\x9d\x01\x2a"


@dataclass(frozen=True, slots=True)
class ImageSize:
    """Medidas en píxeles de una imagen y lo que costaría tenerla en memoria."""

    width: int
    height: int

    @property
    def pixels(self) -> int:
        return self.width * self.height

    @property
    def longest_side(self) -> int:
        return max(self.width, self.height)

    @property
    def estimated_decoded_bytes(self) -> int:
        """Memoria del bitmap resultante; el pico real del decodificador puede ser mayor."""
        return self.pixels * _BYTES_PER_PIXEL


def read_image_size(header: bytes, image_format: ImageFormat) -> ImageSize | None:
    """Devuelve las dimensiones declaradas en la cabecera, o ``None`` si no se pueden leer."""
    if image_format is ImageFormat.PNG:
        return _png_size(header)
    if image_format is ImageFormat.JPEG:
        return _jpeg_size(header)
    if image_format is ImageFormat.WEBP:
        return _webp_size(header)
    return None


def header_bytes_needed() -> int:
    """Cuántos bytes iniciales hay que leer para poder analizar cualquier formato."""
    return _HEADER_BYTES


def read_image_size_from_path(path: Path, image_format: ImageFormat) -> ImageSize | None:
    """Variante que lee el archivo por su cuenta; útil fuera del triaje."""
    return read_image_size(filesystem.read_bytes(path, count=_HEADER_BYTES), image_format)


def _png_size(header: bytes) -> ImageSize | None:
    if len(header) < _PNG_HEADER_END or header[12:16] != b"IHDR":
        return None
    return _validated(int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big"))


def _jpeg_size(header: bytes) -> ImageSize | None:
    indice = 2
    while indice + 1 < len(header):
        if header[indice] != _JPEG_MARKER_PREFIX:
            return None
        marcador = header[indice + 1]
        if marcador == _JPEG_MARKER_PREFIX:
            indice += 1
            continue
        if marcador in _JPEG_STANDALONE_MARKERS:
            indice += 2
            continue
        if marcador in _JPEG_SOF_MARKERS:
            return _jpeg_sof_size(header, indice)
        longitud = int.from_bytes(header[indice + 2 : indice + 4], "big")
        if longitud < _JPEG_MIN_SEGMENT_LENGTH:
            return None
        indice += 2 + longitud
    return None


def _jpeg_sof_size(header: bytes, indice: int) -> ImageSize | None:
    if indice + _JPEG_SOF_HEADER_END > len(header):
        return None
    alto = int.from_bytes(header[indice + 5 : indice + 7], "big")
    ancho = int.from_bytes(header[indice + 7 : indice + 9], "big")
    return _validated(ancho, alto)


def _webp_size(header: bytes) -> ImageSize | None:
    if len(header) < _WEBP_MIN_HEADER:
        return None
    variante = header[12:16]
    if variante == b"VP8X":
        ancho = int.from_bytes(header[24:27], "little") + 1
        alto = int.from_bytes(header[27:30], "little") + 1
        return _validated(ancho, alto)
    if variante == b"VP8L":
        empaquetado = int.from_bytes(header[21:25], "little")
        ancho = (empaquetado & _VP8L_MASK) + 1
        alto = ((empaquetado >> _VP8L_HEIGHT_SHIFT) & _VP8L_MASK) + 1
        return _validated(ancho, alto)
    if variante == b"VP8 " and header[23:26] == _VP8_START_CODE:
        ancho = int.from_bytes(header[26:28], "little") & _VP8L_MASK
        alto = int.from_bytes(header[28:30], "little") & _VP8L_MASK
        return _validated(ancho, alto)
    return None


def _validated(width: int, height: int) -> ImageSize | None:
    if width < 1 or height < 1:
        return None
    return ImageSize(width=width, height=height)
