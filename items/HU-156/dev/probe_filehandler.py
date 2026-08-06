"""Mide si logging.FileHandler sobrevive a las rutas que la capa de ADR-004 rescata."""

import logging
import os
import tempfile
from pathlib import Path

PREFIJO = "\\\\?\\"
base = Path(tempfile.mkdtemp())


def system_path(ruta: Path) -> str:
    """Réplica exacta de media_optimizer.ingest.filesystem.system_path."""
    return PREFIJO + os.path.normpath(str(ruta))


def probar(etiqueta: str, argumento: object) -> None:
    try:
        manejador = logging.FileHandler(argumento, encoding="utf-8")  # type: ignore[arg-type]
        interno = manejador.baseFilename
        manejador.emit(logging.LogRecord("t", 20, "f", 1, "hola", None, None))
        manejador.close()
        print(f"{etiqueta:38} OK   | ruta interna: ...{interno[-28:]}")
    except (OSError, ValueError) as error:
        print(f"{etiqueta:38} FALLA| {type(error).__name__}: {error}")


# 1) ruta larga (383 caracteres)
profunda = base.joinpath(*["x" * 40] * 8)
os.makedirs(system_path(profunda), exist_ok=True)
larga = profunda / "run.log"
probar("larga, tal cual", larga)
probar("larga, ya adaptada por la capa", system_path(larga))

# 2) nombres de dispositivo
for nombre in ("CON.log", "NUL.log", "COM1.log"):
    probar(f"{nombre}, tal cual", base / nombre)
    probar(f"{nombre}, ya adaptada por la capa", system_path(base / nombre))

# 3) confirmar que la ruta adaptada sí guardó bytes de verdad
for nombre in ("CON.log", "NUL.log"):
    ruta = system_path(base / nombre)
    existe = os.path.exists(ruta)
    tam = os.stat(ruta).st_size if existe else "NO EXISTE"
    print(f"bytes realmente en disco para {nombre}: {tam}")
