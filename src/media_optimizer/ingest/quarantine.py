"""Triaje de la carpeta de entrada: qué archivos sirven y por qué se aparta el resto.

En simple: separa lo utilizable de lo que no lo es y anota el motivo de cada
descarte, para que un archivo roto no detenga el lote entero. Apartar es solo
anotarlo en una lista — los archivos del usuario no se mueven, ni se copian, ni
se tocan.

La revisión es estructural: se comprueba la firma del formato y que el archivo
termine donde debe terminar. Una imagen que pase esta revisión todavía puede
fallar al abrirse; eso lo detecta la decodificación más adelante.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from media_optimizer.core import CorruptMediaError
from media_optimizer.ingest import filesystem
from media_optimizer.ingest.dimensions import (
    MAX_DECODED_BYTES,
    MAX_SIDE,
    header_bytes_needed,
    read_image_size,
)
from media_optimizer.ingest.formats import SUPPORTED_FORMATS, ImageFormat, detect_image_format

_TAIL_BYTES = 64
_CLOSING_MARKERS: dict[ImageFormat, bytes] = {
    ImageFormat.JPEG: b"\xff\xd9",
    ImageFormat.PNG: b"IEND\xaeB`\x82",
}
"""Marca de cierre por formato. WebP no aparece: declara su tamaño en la cabecera.

Todo formato de ``SUPPORTED_FORMATS`` debe estar aquí o tratarse antes; si falta,
el ``KeyError`` delata el olvido en desarrollo en vez de aceptar archivos a ciegas.
"""
_WEBP_HEADER_BYTES = 12


class QuarantineReason(StrEnum):
    """Motivo por el que un archivo queda fuera del procesamiento."""

    UNREADABLE = "unreadable"
    EMPTY = "empty"
    UNKNOWN_FORMAT = "unknown_format"
    UNSUPPORTED_FORMAT = "unsupported_format"
    TRUNCATED = "truncated"
    TOO_LARGE = "too_large"


@dataclass(frozen=True, slots=True)
class QuarantinedAsset:
    """Archivo apartado, con su motivo agrupable y una explicación para el usuario."""

    path: Path
    reason: QuarantineReason
    detail: str


@dataclass(frozen=True, slots=True)
class TriageResult:
    """Reparto del lote entre lo que sigue al pipeline y lo que queda fuera."""

    accepted: tuple[Path, ...] = ()
    quarantined: tuple[QuarantinedAsset, ...] = ()


def triage_media(paths: Iterable[Path]) -> TriageResult:
    """Reparte las rutas entre aceptadas y apartadas, sin detenerse ante un fallo.

    Las dos listas salen ordenadas por ruta, así que el resultado no depende del
    orden en que llegaron los archivos.
    """
    aceptados: list[Path] = []
    apartados: list[QuarantinedAsset] = []
    for ruta in paths:
        problema = _classify(ruta)
        if problema is None:
            aceptados.append(ruta)
        else:
            apartados.append(problema)
    return TriageResult(
        accepted=tuple(sorted(aceptados)),
        quarantined=tuple(sorted(apartados, key=lambda asset: asset.path)),
    )


def _classify(path: Path) -> QuarantinedAsset | None:
    """Devuelve el motivo de descarte, o ``None`` si el archivo sirve."""
    try:
        problema = _find_problem(path)
    except CorruptMediaError as error:
        return QuarantinedAsset(path, QuarantineReason.UNREADABLE, error.reason)
    if problema is None:
        return None
    motivo, detalle = problema
    return QuarantinedAsset(path, motivo, detalle)


def _find_problem(path: Path) -> tuple[QuarantineReason, str] | None:
    """Aplica las comprobaciones en orden, de la más barata a la más específica."""
    tamano = _file_size(path)
    if tamano == 0:
        return (QuarantineReason.EMPTY, "el archivo está vacío (0 bytes)")
    formato = detect_image_format(path)
    if formato is None:
        return (
            QuarantineReason.UNKNOWN_FORMAT,
            "el contenido no corresponde a ningún formato de imagen conocido",
        )
    if formato not in SUPPORTED_FORMATS:
        return (
            QuarantineReason.UNSUPPORTED_FORMAT,
            f"formato {formato} reconocido pero no soportado: convertir a JPEG o PNG",
        )
    if _is_truncated(path, formato, tamano):
        return (
            QuarantineReason.TRUNCATED,
            f"el archivo {formato} está incompleto: no llega a su marca de cierre",
        )
    return _check_size_limits(path, formato)


def _check_size_limits(
    path: Path, image_format: ImageFormat
) -> tuple[QuarantineReason, str] | None:
    """Rechaza lo que pediría una memoria desproporcionada, sin abrir la imagen."""
    medida = read_image_size(_read_bytes(path, 0, header_bytes_needed()), image_format)
    if medida is None:
        return None
    if medida.longest_side > MAX_SIDE:
        return (
            QuarantineReason.TOO_LARGE,
            f"{medida.width}x{medida.height} px: el lado mayor supera el máximo de {MAX_SIDE} px",
        )
    if medida.estimated_decoded_bytes > MAX_DECODED_BYTES:
        return (
            QuarantineReason.TOO_LARGE,
            f"{medida.width}x{medida.height} px pediría {_gib(medida.estimated_decoded_bytes)} "
            f"al abrirse; el máximo es {_gib(MAX_DECODED_BYTES)}",
        )
    return None


def _gib(size_in_bytes: int) -> str:
    return f"{size_in_bytes / (1024 * 1024 * 1024):.1f} GiB"


def _file_size(path: Path) -> int:
    try:
        return filesystem.file_size(path)
    except OSError as error:
        raise CorruptMediaError(
            path, f"no se pudo consultar el archivo ({error.strerror})"
        ) from error


def _is_truncated(path: Path, image_format: ImageFormat, size: int) -> bool:
    """Comprueba que el archivo llegue hasta donde su formato dice que debe llegar."""
    if image_format is ImageFormat.WEBP:
        return _webp_declared_size(path) > size
    marcador = _CLOSING_MARKERS[image_format]
    return marcador not in _read_bytes(path, max(0, size - _TAIL_BYTES))


def _webp_declared_size(path: Path) -> int:
    """Tamaño total que declara la cabecera RIFF (el campo cuenta desde el byte 8)."""
    cabecera = _read_bytes(path, 0, _WEBP_HEADER_BYTES)
    return int.from_bytes(cabecera[4:8], "little") + 8


def _read_bytes(path: Path, offset: int, count: int | None = None) -> bytes:
    try:
        return filesystem.read_bytes(path, offset, count)
    except OSError as error:  # pragma: no cover - carrera: el archivo desaparece a mitad del triaje
        raise CorruptMediaError(path, f"no se pudo leer el archivo ({error.strerror})") from error
