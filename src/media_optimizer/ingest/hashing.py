"""Huella de contenido de un archivo y agrupamiento de copias idénticas.

En simple: calcula una firma que depende solo de lo que hay dentro del archivo,
nunca de su nombre ni de dónde esté. Dos copias de la misma foto con nombres
distintos dan la misma firma, y así se detectan sin abrir la imagen. El archivo
se lee por bloques, de modo que un video de gigabytes no se carga a memoria.

"Idéntico" aquí significa byte a byte: dos fotos de la misma escena con metadatos
distintos son archivos distintos — reconocer que muestran lo mismo es otro problema.
"""

import hashlib
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from media_optimizer.core import CorruptMediaError

HASH_ALGORITHM = "sha256"
"""Nombre del algoritmo, para publicarlo junto al hash en el catálogo."""

_CHUNK_BYTES = 1024 * 1024
_MIN_GROUP_SIZE = 2


@dataclass(frozen=True, slots=True)
class DuplicateGroup:
    """Conjunto de archivos que comparten exactamente el mismo contenido."""

    content_hash: str
    paths: tuple[Path, ...]


def compute_content_hash(path: Path) -> str:
    """Devuelve el SHA-256 del archivo en hexadecimal minúscula.

    Comparable directamente con ``sha256sum`` o ``Get-FileHash``.

    Raises:
        CorruptMediaError: si el archivo no se puede leer.
    """
    resumen = hashlib.sha256()
    try:
        with path.open("rb") as archivo:
            while bloque := archivo.read(_CHUNK_BYTES):
                resumen.update(bloque)
    except OSError as error:
        raise CorruptMediaError(path, f"no se pudo leer el archivo ({error.strerror})") from error
    return resumen.hexdigest()


def find_duplicate_groups(paths: Iterable[Path]) -> tuple[DuplicateGroup, ...]:
    """Agrupa las rutas que comparten contenido, en orden estable.

    Solo devuelve los conjuntos con dos o más archivos: un archivo único no es
    un duplicado. Los grupos y sus rutas salen ordenados, así que el resultado
    no depende del orden en que llegaron las rutas.
    """
    por_hash: defaultdict[str, list[Path]] = defaultdict(list)
    for ruta in paths:
        por_hash[compute_content_hash(ruta)].append(ruta)

    grupos = [
        DuplicateGroup(content_hash=huella, paths=tuple(sorted(rutas)))
        for huella, rutas in por_hash.items()
        if len(rutas) >= _MIN_GROUP_SIZE
    ]
    return tuple(sorted(grupos, key=lambda grupo: grupo.paths))
