"""Encuadre vertical: cómo llevar un clip de cualquier forma a 9:16 sin deformarlo.

En simple: los clips llegan apaisados, cuadrados o ya verticales, y el reel se ve
en un teléfono. Aquí se calcula cuánto agrandar cada clip para que **cubra** el
alto y el ancho del destino, y qué trozo recortar del centro. Nunca se estira la
imagen: si sobra ancho se recorta ancho, y si sobra alto se recorta alto.

El cálculo es aritmética pura y exacta —sin decimales que arrastren error entre
corridas—, y las medidas salen siempre pares, que es lo que los codificadores de
video necesitan para no rechazar el cuadro.
"""

from dataclasses import dataclass

ANCHO_VERTICAL = 1080
ALTO_VERTICAL = 1920
CUADROS_POR_SEGUNDO = 30

_REINICIO_DE_TIEMPOS = "setpts=PTS-STARTPTS"
_MINIMO = 2


def _a_par(valor: int) -> int:
    """Sube al par siguiente si hace falta: los codificadores exigen medidas pares."""
    return max(_MINIMO, valor + (valor % 2))


@dataclass(frozen=True, slots=True)
class CropBox:
    """El trozo que se conserva: dónde empieza y cuánto mide."""

    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class VerticalFraming:
    """Cómo encuadrar un clip: a cuánto agrandarlo y qué recortar después."""

    scaled_width: int
    scaled_height: int
    crop: CropBox

    @property
    def crops_width(self) -> bool:
        """Si lo que sobraba era ancho (el clip venía apaisado)."""
        return self.scaled_width > self.crop.width


def frame_to_vertical(
    source_width: int,
    source_height: int,
    target_width: int = ANCHO_VERTICAL,
    target_height: int = ALTO_VERTICAL,
) -> VerticalFraming:
    """Calcula el agrandado y el recorte centrado que llevan el clip al formato vertical.

    Agranda lo justo para cubrir el destino por los dos lados y recorta del centro
    lo que sobra. Nunca deforma: la proporción original se conserva.

    Raises:
        ValueError: si alguna medida no es positiva.
    """
    for nombre, valor in (
        ("source_width", source_width),
        ("source_height", source_height),
        ("target_width", target_width),
        ("target_height", target_height),
    ):
        if valor < 1:
            msg = f"{nombre} debe ser >= 1 px, se recibió {valor}"
            raise ValueError(msg)

    # Comparación en enteros: evita que un decimal decida el encuadre.
    mas_ancho_que_el_destino = source_width * target_height > source_height * target_width
    if mas_ancho_que_el_destino:
        escalado_alto = target_height
        escalado_ancho = round(source_width * target_height / source_height)
    else:
        escalado_ancho = target_width
        escalado_alto = round(source_height * target_width / source_width)

    escalado_ancho = _a_par(max(escalado_ancho, target_width))
    escalado_alto = _a_par(max(escalado_alto, target_height))
    return VerticalFraming(
        scaled_width=escalado_ancho,
        scaled_height=escalado_alto,
        crop=CropBox(
            x=(escalado_ancho - target_width) // 2,
            y=(escalado_alto - target_height) // 2,
            width=target_width,
            height=target_height,
        ),
    )


def vertical_filter_chain(framing: VerticalFraming, *, fps: int = CUADROS_POR_SEGUNDO) -> str:
    """La cadena de filtros que aplica el encuadre, con los tiempos ya reiniciados.

    El reinicio de marcas de tiempo va primero: sin él, al encadenar este clip con
    el siguiente el tiempo salta hacia atrás y el reproductor descarta cuadros.
    """
    recorte = framing.crop
    return ",".join(
        (
            _REINICIO_DE_TIEMPOS,
            f"scale={framing.scaled_width}:{framing.scaled_height}",
            f"crop={recorte.width}:{recorte.height}:{recorte.x}:{recorte.y}",
            f"fps={fps}",
            "format=yuv420p",
        )
    )
