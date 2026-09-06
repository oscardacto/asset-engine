"""Corre el detector de escenas sobre videos reales y deja un reporte por clip.

En simple: busca los videos de una carpeta, los parte en escenas y escribe al
lado de cada uno un archivo con los tiempos exactos de cada corte. Sirve para
ver, con material de verdad, si el umbral está bien calibrado antes de meterlo
en el pipeline.

Por defecto mira en los insumos de la historia, pero acepta cualquier carpeta:
así se puede apuntar a donde los videos ya viven, sin copiarlos al repositorio.

    uv run python scripts/probar_escenas_insumos.py [carpeta] [--umbral 27.0]
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from media_optimizer.core import CorruptMediaError, Scene
from media_optimizer.ingest import filesystem
from media_optimizer.video import UMBRAL_POR_DEFECTO, PySceneDetectAdapter, detect_version

CARPETA_POR_DEFECTO = Path("items/HU-101/insumos")
EXTENSIONES = (".mp4", ".mov", ".mkv", ".avi")
SUFIJO_REPORTE = ".escenas.json"
_VERSION_REPORTE = 1


@dataclass(frozen=True, slots=True)
class Opciones:
    """Lo que se pidió en la línea de comandos, ya con tipos verificables."""

    carpeta: Path
    umbral: float


def _leer_opciones(argv: list[str] | None = None) -> Opciones:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "carpeta",
        nargs="?",
        type=Path,
        default=None,
        help=f"Dónde buscar los videos (por defecto: {CARPETA_POR_DEFECTO}).",
    )
    parser.add_argument(
        "--umbral",
        type=float,
        default=None,
        help=(
            "Cuánto tiene que cambiar la imagen para contar como corte "
            f"(por defecto: {UMBRAL_POR_DEFECTO})."
        ),
    )
    args = parser.parse_args(argv)
    return Opciones(
        carpeta=Path(args.carpeta) if args.carpeta is not None else CARPETA_POR_DEFECTO,
        umbral=float(args.umbral) if args.umbral is not None else UMBRAL_POR_DEFECTO,
    )


def buscar_videos(carpeta: Path) -> tuple[Path, ...]:
    """Los videos de la carpeta, en orden estable."""
    if not filesystem.is_directory(carpeta):
        return ()
    return tuple(
        sorted(
            (ruta for ruta in filesystem.iter_files(carpeta) if ruta.suffix.lower() in EXTENSIONES),
            key=str,
        )
    )


def escribir_reporte(video: Path, escenas: tuple[Scene, ...], umbral: float) -> Path:
    """Deja al lado del video un archivo con los tiempos de cada escena."""
    documento = {
        "version": _VERSION_REPORTE,
        "video": video.name,
        "threshold": umbral,
        "scene_count": len(escenas),
        "scenes": [
            {
                "index": escena.index,
                "start_seconds": escena.start_seconds,
                "end_seconds": escena.end_seconds,
                "duration_seconds": escena.duration_seconds,
            }
            for escena in escenas
        ],
    }
    destino = video.with_name(video.name + SUFIJO_REPORTE)
    texto = json.dumps(documento, indent=2, sort_keys=True, ensure_ascii=False)
    filesystem.write_bytes(destino, (texto + "\n").encode("utf-8"))
    return destino


def main(argv: list[str] | None = None) -> int:
    """Procesa la carpeta y devuelve el código de salida."""
    opciones = _leer_opciones(argv)
    salida = sys.stdout

    version = detect_version()
    salida.write(f"herramienta de video: {version or 'NO DISPONIBLE'}\n")
    salida.write(f"carpeta: {opciones.carpeta}  ·  umbral: {opciones.umbral}\n\n")

    videos = buscar_videos(opciones.carpeta)
    if not videos:
        salida.write("No hay videos en esa carpeta.\n")
        return 0

    detector = PySceneDetectAdapter()
    apartados = 0
    for video in videos:
        try:
            escenas = detector.detect(video, threshold=opciones.umbral)
        except CorruptMediaError as error:
            apartados += 1
            salida.write(f"  {video.name:44} APARTADO: {error}\n")
            continue
        destino = escribir_reporte(video, escenas, opciones.umbral)
        total = sum(escena.duration_seconds for escena in escenas)
        salida.write(
            f"  {video.name:44} {len(escenas):3} escenas  {total:7.2f} s  -> {destino.name}\n"
        )

    salida.write(f"\nProcesados: {len(videos) - apartados} de {len(videos)}")
    salida.write(f" · apartados: {apartados}\n" if apartados else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
