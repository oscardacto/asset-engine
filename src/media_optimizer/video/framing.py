"""Lleva un clip de cualquier forma al formato vertical, sin tocar el original.

En simple: los clips llegan apaisados, cuadrados o ya verticales, y el reel se ve
en un teléfono. Aquí se mide el clip, se calcula cuánto agrandarlo y qué recortar,
y se produce un archivo nuevo con las medidas exactas del destino.

**El original nunca se modifica.** La salida siempre es un archivo aparte.

El comando se construye en una función y se ejecuta en otra a propósito: así el
recorte se puede verificar con valores literales, sin renderizar nada y en
milisegundos. Un encuadre mal calculado se detecta ahí, no después de procesar un
lote entero.

Y como la herramienta abre los archivos por su cuenta, cada ruta pasa antes por
la capa de acceso al disco: está medido que sin eso no encuentra un clip cuya
ruta supere los 260 caracteres.
"""

from pathlib import Path

import cv2

from media_optimizer.core import CorruptMediaError
from media_optimizer.ingest import filesystem
from media_optimizer.video.ffmpeg_executor import build_command, degrade, run
from media_optimizer.video.transforms import (
    CUADROS_POR_SEGUNDO,
    VerticalFraming,
    frame_to_vertical,
    vertical_filter_chain,
)

_ETIQUETA_SALIDA = "outv"
_SIN_DESPLAZAMIENTO = 0


def read_dimensions(video: Path) -> tuple[int, int]:
    """Ancho y alto del clip, en píxeles.

    Lee solo lo necesario para conocer las medidas; no decodifica el clip entero.

    Raises:
        CorruptMediaError: si el clip no se puede abrir o no declara medidas.
    """
    captura = cv2.VideoCapture(filesystem.system_path(video))
    try:
        if not captura.isOpened():
            msg = "no se pudo abrir el clip para medirlo"
            raise CorruptMediaError(video, msg)
        ancho = int(captura.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(captura.get(cv2.CAP_PROP_FRAME_HEIGHT))
    finally:
        captura.release()

    if ancho < 1 or alto < 1:
        msg = f"el clip no declara medidas válidas: {ancho}x{alto}"
        raise CorruptMediaError(video, msg)
    return ancho, alto


def build_crop_command(
    video: Path,
    framing: VerticalFraming,
    output: Path,
    *,
    offset_x: int = _SIN_DESPLAZAMIENTO,
    fps: int = CUADROS_POR_SEGUNDO,
) -> tuple[str, ...]:
    """Arma el comando que produce el clip vertical, sin ejecutarlo.

    ``offset_x`` mueve el recorte respecto del centro. Se acota al margen que
    realmente sobra: pedir más de lo que hay produciría un recorte fuera del
    cuadro y la herramienta rechazaría el clip a mitad del lote.
    """
    cadena = vertical_filter_chain(_desplazado(framing, offset_x), fps=fps)
    return build_command(
        [video],
        f"[0:v]{cadena}[{_ETIQUETA_SALIDA}]",
        output,
        output_label=_ETIQUETA_SALIDA,
    )


def crop_to_vertical(
    video: Path,
    output: Path,
    *,
    offset_x: int = _SIN_DESPLAZAMIENTO,
    fps: int = CUADROS_POR_SEGUNDO,
) -> VerticalFraming:
    """Produce el clip vertical y devuelve el encuadre que se aplicó.

    Devuelve el encuadre y no solo un éxito porque quien llama necesita poder
    explicar después qué parte del material se recortó.

    Raises:
        CorruptMediaError: si el clip no se puede leer o la herramienta lo rechaza.
    """
    encuadre = frame_to_vertical(*read_dimensions(video))
    resultado = run(build_crop_command(video, encuadre, output, offset_x=offset_x, fps=fps))
    if not resultado.ok:
        raise degrade(video, resultado)
    return _desplazado(encuadre, offset_x)


def _desplazado(framing: VerticalFraming, offset_x: int) -> VerticalFraming:
    """El mismo encuadre movido, sin salirse nunca del material."""
    if offset_x == _SIN_DESPLAZAMIENTO:
        return framing
    margen = framing.scaled_width - framing.crop.width
    horizontal = min(max(framing.crop.x + offset_x, _SIN_DESPLAZAMIENTO), margen)
    recorte = framing.crop
    return VerticalFraming(
        scaled_width=framing.scaled_width,
        scaled_height=framing.scaled_height,
        crop=type(recorte)(x=horizontal, y=recorte.y, width=recorte.width, height=recorte.height),
    )
