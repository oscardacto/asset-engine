"""Lectura tolerante de los metadatos EXIF de una foto.

En simple: saca del archivo dos datos que el resto del sistema necesita —cómo
estaba girada la cámara y cuándo se tomó la foto— sin que un bloque de metadatos
roto pueda detener el lote. Si el EXIF falta o viene corrupto, se devuelve lo que
se haya podido leer y se marca como incompleto; la foto sigue siendo utilizable.

Como el resto de esta capa, nunca abre la imagen: busca los metadatos en los
primeros bytes del archivo. Abrirla para leer una fecha costaría cientos de MB en
una foto de móvil moderno.

Ojo con la orientación: no es un dato pasivo. Al abrir la imagen, OpenCV la gira
según ese valor, así que las medidas leídas de la cabecera y las de la imagen ya
abierta pueden no coincidir. ``oriented_size`` traduce de unas a otras.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Literal

from media_optimizer.ingest import filesystem
from media_optimizer.ingest.dimensions import ImageSize, header_bytes_needed

ByteOrder = Literal["little", "big"]

_APP1_MARKER = 0xE1
_EXIF_SIGNATURE = b"Exif\x00\x00"
_JPEG_MARKER_PREFIX = 0xFF
_JPEG_STANDALONE_MARKERS = frozenset({0x01, *range(0xD0, 0xDA)})
_JPEG_MIN_SEGMENT_LENGTH = 2
_TIFF_LITTLE_ENDIAN = b"II"
_TIFF_BIG_ENDIAN = b"MM"
_TIFF_MAGIC = 42
_TIFF_HEADER_SIZE = 8
_IFD_ENTRY_SIZE = 12
_MAX_IFD_ENTRIES = 512
_TAG_ORIENTATION = 0x0112
_ORIENTATION_UNSET = 0
"""Muchas cámaras escriben la etiqueta con valor 0 para decir "sin declarar".

No es un metadato roto: es la ausencia de dato, y se trata igual que si la
etiqueta no estuviera. Solo los valores fuera de 0-8 indican corrupción real.
"""
_TAG_EXIF_POINTER = 0x8769
_TAG_DATETIME_ORIGINAL = 0x9003
_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
_DATETIME_LENGTH = 19


class ExifOrientation(IntEnum):
    """Cómo estaba girada la cámara, según el estándar EXIF (valores 1 a 8)."""

    NORMAL = 1
    MIRROR_HORIZONTAL = 2
    ROTATE_180 = 3
    MIRROR_VERTICAL = 4
    MIRROR_HORIZONTAL_ROTATE_270 = 5
    ROTATE_90 = 6
    MIRROR_HORIZONTAL_ROTATE_90 = 7
    ROTATE_270 = 8

    @property
    def swaps_axes(self) -> bool:
        """Indica si al enderezar la foto se intercambian ancho y alto."""
        return self >= ExifOrientation.MIRROR_HORIZONTAL_ROTATE_270


@dataclass(frozen=True, slots=True)
class ExifData:
    """Lo que se pudo leer del EXIF, con constancia de si venía completo."""

    orientation: ExifOrientation | None = None
    captured_at: datetime | None = None
    is_present: bool = False
    is_malformed: bool = False


def read_exif(path: Path) -> ExifData:
    """Lee el EXIF de una foto sin lanzar por metadatos inválidos o ausentes."""
    return read_exif_from_header(filesystem.read_bytes(path, count=header_bytes_needed()))


def read_exif_from_header(header: bytes) -> ExifData:
    """Variante sobre bytes ya leídos, para no releer el archivo."""
    crudo = _find_exif_block(header)
    if crudo is None:
        return ExifData()
    return _parse_exif(crudo)


def oriented_size(size: ImageSize, orientation: ExifOrientation | None) -> ImageSize:
    """Traduce medidas crudas a las que tendrá la imagen ya enderezada."""
    if orientation is None or not orientation.swaps_axes:
        return size
    return ImageSize(width=size.height, height=size.width)


def _find_exif_block(header: bytes) -> bytes | None:
    """Busca el segmento APP1 con la firma EXIF recorriendo los segmentos JPEG."""
    indice = 2
    while indice + 3 < len(header):
        if header[indice] != _JPEG_MARKER_PREFIX:
            return None
        marcador = header[indice + 1]
        if marcador == _JPEG_MARKER_PREFIX:
            indice += 1
            continue
        if marcador in _JPEG_STANDALONE_MARKERS:
            indice += 2
            continue
        longitud = int.from_bytes(header[indice + 2 : indice + 4], "big")
        if longitud < _JPEG_MIN_SEGMENT_LENGTH:
            return None
        if marcador == _APP1_MARKER:
            cuerpo = header[indice + 4 : indice + 2 + longitud]
            if cuerpo.startswith(_EXIF_SIGNATURE):
                return cuerpo[len(_EXIF_SIGNATURE) :]
        indice += 2 + longitud
    return None


def _parse_exif(raw: bytes) -> ExifData:
    orden = _byte_order(raw)
    if orden is None:
        return ExifData(is_present=True, is_malformed=True)

    principal = _read_ifd(raw, int.from_bytes(raw[4:8], orden), orden)
    if principal is None:
        return ExifData(is_present=True, is_malformed=True)

    entradas, incompleto = principal
    orientacion, orientacion_invalida = _extract_orientation(entradas, orden)
    fecha, fecha_invalida = _extract_captured_at(raw, entradas, orden)
    return ExifData(
        orientation=orientacion,
        captured_at=fecha,
        is_present=True,
        is_malformed=incompleto or orientacion_invalida or fecha_invalida,
    )


def _byte_order(raw: bytes) -> ByteOrder | None:
    if len(raw) < _TIFF_HEADER_SIZE:
        return None
    marca = raw[:2]
    orden: ByteOrder
    if marca == _TIFF_LITTLE_ENDIAN:
        orden = "little"
    elif marca == _TIFF_BIG_ENDIAN:
        orden = "big"
    else:
        return None
    if int.from_bytes(raw[2:4], orden) != _TIFF_MAGIC:
        return None
    return orden


def _read_ifd(raw: bytes, offset: int, order: ByteOrder) -> tuple[dict[int, bytes], bool] | None:
    """Lee un directorio de entradas. ``None`` si el desplazamiento no es utilizable."""
    if offset < _TIFF_HEADER_SIZE or offset + 2 > len(raw):
        return None
    total = int.from_bytes(raw[offset : offset + 2], order)
    if total > _MAX_IFD_ENTRIES:
        return None
    entradas: dict[int, bytes] = {}
    incompleto = False
    for indice in range(total):
        inicio = offset + 2 + indice * _IFD_ENTRY_SIZE
        if inicio + _IFD_ENTRY_SIZE > len(raw):
            incompleto = True
            break
        etiqueta = int.from_bytes(raw[inicio : inicio + 2], order)
        entradas[etiqueta] = raw[inicio + 8 : inicio + _IFD_ENTRY_SIZE]
    return entradas, incompleto


def _extract_orientation(
    entries: dict[int, bytes], order: ByteOrder
) -> tuple[ExifOrientation | None, bool]:
    crudo = entries.get(_TAG_ORIENTATION)
    if crudo is None:
        return None, False
    valor = int.from_bytes(crudo[:2], order)
    if valor == _ORIENTATION_UNSET:
        return None, False
    try:
        return ExifOrientation(valor), False
    except ValueError:
        return None, True


def _extract_captured_at(
    raw: bytes, entries: dict[int, bytes], order: ByteOrder
) -> tuple[datetime | None, bool]:
    puntero = entries.get(_TAG_EXIF_POINTER)
    if puntero is None:
        return None, False
    sub = _read_ifd(raw, int.from_bytes(puntero, order), order)
    if sub is None:
        return None, True
    desplazamiento = sub[0].get(_TAG_DATETIME_ORIGINAL)
    if desplazamiento is None:
        return None, False
    inicio = int.from_bytes(desplazamiento, order)
    if inicio + _DATETIME_LENGTH > len(raw):
        return None, True
    try:
        texto = raw[inicio : inicio + _DATETIME_LENGTH].decode("ascii")
        return datetime.strptime(texto, _DATETIME_FORMAT), False
    except (UnicodeDecodeError, ValueError):
        return None, True
