"""Única puerta del sistema hacia el disco.

En simple: todo el proyecto pide archivos por aquí, y aquí se traduce la ruta a
la forma que el sistema operativo necesita para acceder de verdad. En Windows
hay nombres perfectamente válidos —los que coinciden con dispositivos antiguos
como ``CON``, los que terminan en punto o espacio, y las rutas muy largas— que
por la vía habitual fallan, devuelven vacío o **dejan el proceso colgado**. Con
la forma extendida funcionan todos.

Ningún otro módulo debe abrir archivos ni consultar el disco por su cuenta: esa
regla la vigila ``tests/test_arquitectura.py``. Y la forma extendida no sale de
aquí — las rutas que este módulo devuelve son las normales, presentables y
comparables.
"""

import os
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import IO

_PREFIJO_EXTENDIDO = "\\\\?\\"
_ES_WINDOWS = sys.platform == "win32"


def system_path(path: Path) -> str:
    """Ruta en la forma que exige la plataforma para un acceso fiable.

    En Windows: absoluta, normalizada y con prefijo extendido. En el resto: la
    ruta tal cual. Aplicarla dos veces da el mismo resultado.

    La normalización es **puramente textual** a propósito. Tanto ``Path.resolve()``
    como ``os.path.abspath()`` preguntan al sistema operativo, y este reinterpreta
    los nombres que coinciden con dispositivos antiguos: un archivo llamado
    ``CON.jpg`` se convierte en ``CON`` o en ``\\\\.\\CON`` y deja de poder abrirse.
    Es decir, destruyen justo el nombre que el prefijo viene a rescatar.
    """
    if not _ES_WINDOWS:
        return str(path)
    texto = str(path)
    if texto.startswith(_PREFIJO_EXTENDIDO):
        return texto
    if not path.is_absolute():
        texto = str(Path.cwd()) + os.sep + texto
    return _PREFIJO_EXTENDIDO + os.path.normpath(texto)


def open_binary(path: Path) -> IO[bytes]:
    """Abre el archivo en binario para lectura."""
    return open(system_path(path), "rb")  # noqa: PTH123 - se abre la cadena ya adaptada


def read_bytes(path: Path, offset: int = 0, count: int | None = None) -> bytes:
    """Lee ``count`` bytes desde ``offset``; hasta el final si no se indica."""
    with open_binary(path) as archivo:
        if offset:
            archivo.seek(offset)
        return archivo.read() if count is None else archivo.read(count)


def write_bytes(path: Path, data: bytes) -> None:
    """Escribe el contenido completo, reemplazando lo que hubiera."""
    with open(system_path(path), "wb") as archivo:  # noqa: PTH123
        archivo.write(data)


def file_size(path: Path) -> int:
    """Tamaño en bytes."""
    return os.stat(system_path(path)).st_size  # noqa: PTH116 - cadena ya adaptada


def exists(path: Path) -> bool:
    """Indica si la ruta existe."""
    return os.path.exists(system_path(path))  # noqa: PTH110


def is_directory(path: Path) -> bool:
    """Indica si la ruta es una carpeta."""
    return os.path.isdir(system_path(path))  # noqa: PTH112


def is_file(path: Path) -> bool:
    """Indica si la ruta es un archivo."""
    return os.path.isfile(system_path(path))  # noqa: PTH113


def make_directory(path: Path) -> None:
    """Crea la carpeta y las que falten por encima. Repetirlo no cambia nada."""
    os.makedirs(system_path(path), exist_ok=True)  # noqa: PTH103 - cadena ya adaptada


def replace_atomic(source: Path, target: Path) -> None:
    """Sustituye ``target`` por ``source`` en un solo paso indivisible.

    Ambos deben estar en el mismo volumen: así el destino nunca queda a medias.
    """
    os.replace(system_path(source), system_path(target))  # noqa: PTH105 - cadenas ya adaptadas


def iter_files(root: Path, *, recursive: bool = True) -> Iterator[Path]:
    """Archivos bajo ``root``, sin seguir enlaces de carpeta ni entrar en ocultos.

    Las rutas que devuelve son normales, no las extendidas de uso interno.
    """
    raiz_sistema = Path(system_path(root))
    if recursive:
        yield from _recorrer_arbol(root, raiz_sistema)
    else:
        yield from _listar_nivel(root, raiz_sistema)


def _recorrer_arbol(root: Path, raiz_sistema: Path) -> Iterator[Path]:
    for carpeta, subcarpetas, archivos in raiz_sistema.walk(follow_symlinks=False):
        subcarpetas[:] = [nombre for nombre in subcarpetas if not _es_oculto(nombre)]
        for nombre in archivos:
            if not _es_oculto(nombre):
                yield _sin_prefijo(carpeta / nombre, root, raiz_sistema)


def _listar_nivel(root: Path, raiz_sistema: Path) -> Iterator[Path]:
    for entrada in raiz_sistema.iterdir():
        if not _es_oculto(entrada.name) and os.path.isfile(entrada):  # noqa: PTH113
            yield _sin_prefijo(entrada, root, raiz_sistema)


def _sin_prefijo(ruta_sistema: Path, root: Path, raiz_sistema: Path) -> Path:
    """Devuelve la ruta re-anclada en la raíz original, sin la forma extendida."""
    return root / ruta_sistema.relative_to(raiz_sistema)


def _es_oculto(name: str) -> bool:
    return name.startswith(".")
