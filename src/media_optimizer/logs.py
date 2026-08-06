"""Rastro estructurado: cómo el sistema deja constancia de lo que hace.

En simple: en vez de imprimir frases sueltas, cada evento se escribe como una
línea de JSON con su hora, su nivel y los datos que lo acompañan. Así el rastro se
puede leer a ojo y también filtrar con herramientas, sin inventar un parser.

**Por qué hay un handler propio y no se usa el de la biblioteca estándar.** El
`FileHandler` de Python normaliza la ruta por dentro con ``os.path.abspath``, que
es justo la función que destruye los nombres que la capa de acceso al disco viene a
rescatar. Medido en esta máquina: con un archivo de log en una ruta larga falla;
con ``CON.log`` levanta un error incomprensible; y con ``NUL.log`` **no protesta y
tira todos los registros al dispositivo nulo**. Un sistema de diagnóstico que dice
que todo va bien mientras descarta cada línea es peor que uno que se cae, porque no
deja señal de que falte algo. Pasando la ruta por la capa, los cuatro casos escriben
bien.
"""

import json
import logging
from collections.abc import Mapping
from pathlib import Path
from typing import IO, Any

from media_optimizer.ingest import filesystem

CAMPOS_RESERVADOS = ("timestamp", "level", "logger", "message")
_MARCA = "%Y-%m-%dT%H:%M:%S"
_ATRIBUTOS_DE_LOGGING = frozenset(vars(logging.LogRecord("", 0, "", 0, "", None, None)))


class JsonLinesFormatter(logging.Formatter):
    """Convierte cada registro en una línea de JSON con las claves ordenadas.

    El orden no es estético: los campos varían de un evento a otro, y ordenarlos
    hace que dos líneas equivalentes se lean y se comparen igual.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Devuelve el registro como una sola línea de JSON."""
        evento: dict[str, Any] = {
            "timestamp": f"{self.formatTime(record, _MARCA)}.{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            evento["error"] = self.formatException(record.exc_info)
        for clave, valor in _campos_del_llamador(record).items():
            evento[clave] = valor
        return json.dumps(evento, sort_keys=True, ensure_ascii=False, default=str)


class FilesystemFileHandler(logging.FileHandler):
    """Escribe el log a un archivo pasando la ruta por la capa de acceso al disco.

    Es la única diferencia con el handler de la biblioteca estándar, y es la que
    evita que los registros se pierdan cuando la ruta es larga o el nombre coincide
    con un dispositivo del sistema.
    """

    def __init__(self, path: Path, *, encoding: str = "utf-8") -> None:
        filesystem.make_directory(path.parent)
        super().__init__(filesystem.system_path(path), encoding=encoding)


def configure_logging(
    level: int = logging.INFO,
    *,
    stream: IO[str] | None = None,
    log_file: Path | None = None,
) -> logging.Logger:
    """Deja el rastro del proyecto listo para usarse y devuelve su logger raíz.

    Llamarla más de una vez no duplica nada: reemplaza la configuración anterior en
    vez de acumularla, así un comando que la invoque dos veces no escribe cada línea
    dos veces.
    """
    raiz = logging.getLogger("media_optimizer")
    for anterior in tuple(raiz.handlers):
        raiz.removeHandler(anterior)
        anterior.close()

    formato = JsonLinesFormatter()
    destinos: list[logging.Handler] = [logging.StreamHandler(stream)]
    if log_file is not None:
        destinos.append(FilesystemFileHandler(log_file))
    for destino in destinos:
        destino.setFormatter(formato)
        raiz.addHandler(destino)

    raiz.setLevel(level)
    raiz.propagate = False
    return raiz


def get_logger(name: str) -> logging.Logger:
    """Logger de un módulo, colgando del raíz del proyecto."""
    return logging.getLogger(f"media_optimizer.{name}")


def _campos_del_llamador(record: logging.LogRecord) -> Mapping[str, Any]:
    """Los datos que el llamador pasó con ``extra``, sin los internos de logging.

    Un campo que choque con uno reservado se descarta: nadie debería poder falsear
    el nivel o la hora de su propio evento desde ``extra``.
    """
    return {
        clave: valor
        for clave, valor in vars(record).items()
        if clave not in _ATRIBUTOS_DE_LOGGING and clave not in CAMPOS_RESERVADOS
    }
