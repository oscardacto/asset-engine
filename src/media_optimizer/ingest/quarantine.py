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
from media_optimizer.ingest.formats import SUPPORTED_FORMATS, ImageFormat, detect_image_format

_TAIL_BYTES = 64
_CLOSING_MARKERS: dict[ImageFormat, bytes] = {
    ImageFormat.JPEG: b"\xff\xd9",
    ImageFormat.PNG: b"IEND\xaeB`\x82",
}
_WEBP_HEADER_BYTES = 12


class QuarantineReason(StrEnum):
    """Motivo por el que un archivo queda fuera del procesamiento."""

    UNREADABLE = "unreadable"
    EMPTY = "empty"
    UNKNOWN_FORMAT = "unknown_format"
    UNSUPPORTED_FORMAT = "unsupported_format"
    TRUNCATED = "truncated"


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
        tamano = _file_size(path)
        formato = detect_image_format(path)
        truncado = tamano > 0 and formato is not None and _is_truncated(path, formato, tamano)
    except CorruptMediaError as error:
        return QuarantinedAsset(path, QuarantineReason.UNREADABLE, error.reason)

    if tamano == 0:
        return QuarantinedAsset(path, QuarantineReason.EMPTY, "el archivo está vacío (0 bytes)")
    if formato is None:
        return QuarantinedAsset(
            path,
            QuarantineReason.UNKNOWN_FORMAT,
            "el contenido no corresponde a ningún formato de imagen conocido",
        )
    if formato not in SUPPORTED_FORMATS:
        return QuarantinedAsset(
            path,
            QuarantineReason.UNSUPPORTED_FORMAT,
            f"formato {formato} reconocido pero no soportado: convertir a JPEG o PNG",
        )
    if truncado:
        return QuarantinedAsset(
            path,
            QuarantineReason.TRUNCATED,
            f"el archivo {formato} está incompleto: no llega a su marca de cierre",
        )
    return None


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError as error:
        raise CorruptMediaError(
            path, f"no se pudo consultar el archivo ({error.strerror})"
        ) from error


def _is_truncated(path: Path, image_format: ImageFormat, size: int) -> bool:
    """Comprueba que el archivo llegue hasta donde su formato dice que debe llegar."""
    if image_format is ImageFormat.WEBP:
        return _webp_declared_size(path) > size
    marcador = _CLOSING_MARKERS.get(image_format)
    if marcador is None:
        return False
    return marcador not in _read_bytes(path, max(0, size - _TAIL_BYTES))


def _webp_declared_size(path: Path) -> int:
    """Tamaño total que declara la cabecera RIFF (el campo cuenta desde el byte 8)."""
    cabecera = _read_bytes(path, 0, _WEBP_HEADER_BYTES)
    return int.from_bytes(cabecera[4:8], "little") + 8


def _read_bytes(path: Path, offset: int, count: int | None = None) -> bytes:
    try:
        with path.open("rb") as archivo:
            archivo.seek(offset)
            return archivo.read() if count is None else archivo.read(count)
    except OSError as error:  # pragma: no cover - carrera: el archivo desaparece a mitad del triaje
        raise CorruptMediaError(path, f"no se pudo leer el archivo ({error.strerror})") from error
