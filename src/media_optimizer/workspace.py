"""Directorio de trabajo: dónde van las salidas y por qué los originales no se tocan.

En simple: el programa nunca escribe en tu carpeta de fotos. Todo lo que produce
va a un directorio aparte que tú eliges, y hay una función que comprueba —no que
promete— que tus archivos quedaron exactamente como estaban.

También traduce los nombres de entrada a nombres de salida seguros. Es el
problema **inverso** al de la capa de acceso: allí había que poder *leer*
cualquier nombre que el sistema admita; aquí hay que evitar *crear* nombres que
después nadie pueda abrir. Y hay una trampa medida: en Windows, ``Foto.jpg`` y
``foto.jpg`` no pueden coexistir — el segundo pisa al primero sin avisar—, así
que dos fotos distintas podrían acabar en el mismo archivo de salida.
"""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from media_optimizer.ingest import filesystem
from media_optimizer.ingest.hashing import compute_content_hash

REPORTS_DIRNAME = "reports"

_CARACTERES_PROHIBIDOS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_NOMBRES_DE_DISPOSITIVO = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{numero}" for numero in range(1, 10)),
        *(f"LPT{numero}" for numero in range(1, 10)),
    }
)
_SUSTITUTO = "_"
_NOMBRE_POR_DEFECTO = "sin_nombre"
_LARGO_MAXIMO = 200
_SUFIJO_INICIAL = 2


@dataclass(frozen=True, slots=True)
class Workspace:
    """Carpeta donde el programa deja todo lo que produce."""

    root: Path

    @property
    def reports_dir(self) -> Path:
        """Carpeta de reportes legibles."""
        return self.root / REPORTS_DIRNAME

    def ensure(self) -> None:
        """Crea las carpetas que falten. Ejecutarlo dos veces no cambia nada."""
        filesystem.make_directory(self.root)
        filesystem.make_directory(self.reports_dir)


@dataclass(frozen=True, slots=True)
class SourceFingerprint:
    """Huella de los archivos de origen, para poder demostrar que no se tocaron."""

    hashes: tuple[tuple[str, str], ...]


def fingerprint_sources(paths: tuple[Path, ...]) -> SourceFingerprint:
    """Toma la huella de cada archivo de origen antes de escribir nada."""
    return SourceFingerprint(
        hashes=tuple(sorted((str(ruta), compute_content_hash(ruta)) for ruta in paths))
    )


def find_modified_sources(fingerprint: SourceFingerprint) -> tuple[str, ...]:
    """Devuelve los orígenes cuyo contenido cambió. Vacío significa intactos."""
    return tuple(
        ruta for ruta, huella in fingerprint.hashes if compute_content_hash(Path(ruta)) != huella
    )


def safe_output_name(name: str, taken: frozenset[str] = frozenset()) -> str:
    """Convierte un nombre de entrada en uno escribible y sin colisión.

    ``taken`` son los nombres de salida ya usados; la comparación ignora
    mayúsculas, porque en Windows dos nombres que solo difieren en la caja se
    pisan entre sí.
    """
    base = _sanear(name)
    if base.casefold() not in {usado.casefold() for usado in taken}:
        return base
    return _desambiguar(base, taken)


def _sanear(name: str) -> str:
    limpio = unicodedata.normalize("NFC", name)
    limpio = _CARACTERES_PROHIBIDOS.sub(_SUSTITUTO, limpio)
    limpio = limpio.rstrip(". ")
    if not limpio:
        return _NOMBRE_POR_DEFECTO
    if _tronco(limpio).upper() in _NOMBRES_DE_DISPOSITIVO:
        limpio = f"{_SUSTITUTO}{limpio}"
    return limpio[:_LARGO_MAXIMO].rstrip(". ") or _NOMBRE_POR_DEFECTO


def _tronco(name: str) -> str:
    """Nombre sin su extensión: es lo que Windows compara con los dispositivos."""
    tronco, punto, _ = name.rpartition(".")
    return tronco if punto else name


def _desambiguar(base: str, taken: frozenset[str]) -> str:
    usados = {nombre.casefold() for nombre in taken}
    tronco, punto, extension = base.rpartition(".")
    if not punto:
        tronco, extension = base, ""
    sufijo = _SUFIJO_INICIAL
    while True:
        candidato = f"{tronco}_{sufijo}{'.' + extension if extension else ''}"
        if candidato.casefold() not in usados:
            return candidato
        sufijo += 1
