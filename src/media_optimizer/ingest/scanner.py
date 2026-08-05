"""Escaneo de la carpeta de entrada: lista los archivos candidatos en orden estable.

En simple: mira qué hay en la carpeta que dio el usuario y devuelve la lista de
archivos siempre en el mismo orden, sin importar el sistema operativo ni cómo el
disco los enumere. No abre ni modifica nada: solo mira nombres.
"""

import unicodedata
from pathlib import Path

from media_optimizer.core import InvalidInputError
from media_optimizer.ingest import filesystem


def scan_input_folder(root: Path, recursive: bool = True) -> tuple[Path, ...]:
    """Devuelve los archivos de ``root`` en orden determinista.

    Incluye todo archivo visible sin filtrar por extensión —decidir qué es un
    medio válido corresponde a la validación de formato—, omite directorios y
    entradas ocultas, y no sigue enlaces simbólicos de carpeta (evita ciclos).
    Una subcarpeta ilegible se omite y el recorrido continúa.

    Raises:
        InvalidInputError: si la ruta no existe o no es una carpeta.
    """
    _validate_root(root)
    encontrados = filesystem.iter_files(root, recursive=recursive)
    return tuple(sorted(encontrados, key=lambda ruta: _sort_key(ruta, root)))


def _validate_root(root: Path) -> None:
    if not filesystem.exists(root):
        msg = f"la carpeta de entrada no existe: {root}"
        raise InvalidInputError(msg)
    if not filesystem.is_directory(root):
        msg = f"la ruta de entrada no es una carpeta: {root}"
        raise InvalidInputError(msg)


def _sort_key(path: Path, root: Path) -> tuple[str, str, str]:
    """Clave de orden estable: forma Unicode fija, sin distinguir caja, con desempates."""
    cruda = path.relative_to(root).as_posix()
    normalizada = unicodedata.normalize("NFC", cruda)
    return (normalizada.casefold(), normalizada, cruda)
