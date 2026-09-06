"""Única puerta hacia el procesamiento de video: invoca el binario externo.

En simple: armar un video —recortar clips, encadenarlos, poner transiciones— lo
hace una herramienta externa que se ejecuta como un programa aparte. Aquí se
construye lo que hay que pedirle y se interpreta lo que responde.

**Por qué las reglas de determinismo viven aquí y no en quien llama.** El programa
promete que el mismo material produce el mismo video. En video eso no sale gratis:
si el grafo de filtros se reparte entre varios hilos, dos corridas pueden diferir;
y un trozo recortado conserva las marcas de tiempo de su origen, así que al
encadenarlo con otro se producen saltos hacia atrás en el tiempo —el reproductor
descarta cuadros y el sonido se desfasa—. Ambas cosas se arreglan con banderas que
es fácil olvidar. Por eso el llamador no las escribe: se añaden solas.

También se puede **probar un grafo de filtros sin renderizar nada**: se le da una
fuente sintética y se tira el resultado, así un error de sintaxis aparece en
milisegundos en vez de después de minutos de cómputo.
"""

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from media_optimizer.core import CorruptMediaError
from media_optimizer.ingest import filesystem
from media_optimizer.logs import get_logger

BINARIO = "ffmpeg"
NORMALIZAR_TIEMPOS_VIDEO = "setpts=PTS-STARTPTS"
NORMALIZAR_TIEMPOS_AUDIO = "asetpts=PTS-STARTPTS"
_TIEMPO_LIMITE_SEGUNDOS = 900
_DURACION_DE_PRUEBA = "5"
_FUENTE_SINTETICA = "nullsrc=s=1080x1920:r=30"

# Banderas que hacen reproducible cualquier invocación. No son opcionales.
_DETERMINISMO = (
    "-nostdin",
    "-nostats",
    "-hide_banner",
    "-filter_complex_threads",
    "1",
)


@dataclass(frozen=True, slots=True)
class FfmpegResult:
    """Lo que devolvió la herramienta: si funcionó, qué dijo y qué se le pidió."""

    ok: bool
    stderr: str
    command: tuple[str, ...]

    @property
    def failure_reason(self) -> str:
        """La última línea del error, que es la que dice qué pasó."""
        lineas = [linea.strip() for linea in self.stderr.splitlines() if linea.strip()]
        return lineas[-1] if lineas else "la herramienta de video falló sin explicación"


def is_available() -> bool:
    """Indica si el binario de video está instalado en esta máquina."""
    return filesystem.find_executable(BINARIO) is not None


def normalized_segment(filtros: Sequence[str], *, con_audio: bool = False) -> str:
    """Encadena filtros poniendo delante el reinicio de marcas de tiempo.

    El reinicio va primero y siempre: sin él, al encadenar dos trozos el tiempo
    salta hacia atrás y el reproductor descarta cuadros.
    """
    cabeza = [NORMALIZAR_TIEMPOS_VIDEO]
    if con_audio:
        cabeza.append(NORMALIZAR_TIEMPOS_AUDIO)
    return ",".join([*cabeza, *filtros])


def build_command(
    inputs: Sequence[Path],
    filter_complex: str,
    output: Path,
    *,
    output_label: str = "outv",
) -> tuple[str, ...]:
    """Arma la petición completa, con las banderas de reproducibilidad ya puestas.

    Las rutas se traducen a la forma que el sistema necesita para abrirlas de
    verdad: la herramienta abre los archivos por su cuenta y no aplicaría esa
    traducción sola.
    """
    argumentos: list[str] = [BINARIO, *_DETERMINISMO, "-y"]
    for entrada in inputs:
        argumentos += ["-i", filesystem.system_path(entrada)]
    argumentos += [
        "-filter_complex",
        filter_complex,
        "-map",
        f"[{output_label}]",
        "-map_metadata",
        "-1",
        filesystem.system_path(output),
    ]
    return tuple(argumentos)


def build_probe_command(filter_complex: str, *, output_label: str = "outv") -> tuple[str, ...]:
    """Arma una petición que valida el grafo sin producir ningún archivo.

    Usa una fuente generada y tira el resultado: comprueba la sintaxis y que los
    filtros existan, en milisegundos y sin escribir en disco.
    """
    return (
        BINARIO,
        *_DETERMINISMO,
        "-f",
        "lavfi",
        "-i",
        _FUENTE_SINTETICA,
        "-t",
        _DURACION_DE_PRUEBA,
        "-filter_complex",
        filter_complex,
        "-map",
        f"[{output_label}]",
        "-f",
        "null",
        "-",
    )


def run(command: Sequence[str]) -> FfmpegResult:
    """Ejecuta la petición y devuelve el resultado sin lanzar excepción.

    Un fallo de la herramienta no interrumpe el lote: se registra y quien llama
    decide si aparta ese clip y sigue con los demás.
    """
    registro = get_logger("video")
    try:
        completado = subprocess.run(  # noqa: S603 - lista de argumentos, nunca shell
            list(command),
            capture_output=True,
            text=True,
            check=False,
            timeout=_TIEMPO_LIMITE_SEGUNDOS,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        mensaje = f"la herramienta de video '{BINARIO}' no está instalada"
        registro.error(mensaje)
        return FfmpegResult(ok=False, stderr=mensaje, command=tuple(command))
    except subprocess.TimeoutExpired:
        mensaje = f"la herramienta de video superó el límite de {_TIEMPO_LIMITE_SEGUNDOS} s"
        registro.error(mensaje)
        return FfmpegResult(ok=False, stderr=mensaje, command=tuple(command))

    resultado = FfmpegResult(
        ok=completado.returncode == 0,
        stderr=completado.stderr or "",
        command=tuple(command),
    )
    if not resultado.ok:
        registro.warning(
            "la herramienta de video rechazó la petición",
            extra={"reason": resultado.failure_reason, "exit_code": completado.returncode},
        )
    return resultado


def probe_filtergraph(filter_complex: str, *, output_label: str = "outv") -> FfmpegResult:
    """Comprueba que un grafo de filtros es válido, sin renderizar nada."""
    return run(build_probe_command(filter_complex, output_label=output_label))


def degrade(source: Path, result: FfmpegResult) -> CorruptMediaError:
    """Convierte un fallo de la herramienta en el error que aparta ese clip.

    Devuelve la excepción en vez de lanzarla: quien llama decide si aparta el
    clip y continúa con el lote, que es lo que el pipeline hace.
    """
    return CorruptMediaError(source, result.failure_reason)
