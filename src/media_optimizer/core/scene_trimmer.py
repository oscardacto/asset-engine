"""Ajusta un conjunto de tomas para que dure exactamente lo que pide el formato.

En simple: un reel de quince segundos tiene que durar quince segundos. Aquí se
decide qué tramo de cada escena se usa para que la suma cierre justo.

**La cuenta se hace en milisegundos enteros, no en segundos con decimales.** No es
un capricho: recortar tres escenas proporcionalmente a quince segundos con números
decimales da 15.000000000000002, y un reel que promete quince y dura eso falla
cualquier comparación exacta. Con enteros la suma cierra siempre, y el sobrante de
la división se le da a una sola escena — un milisegundo, imperceptible a treinta
cuadros por segundo.

**Lo que falta no se inventa.** Si las tomas suman nueve segundos y se piden
quince, se devuelven nueve. Llegar a quince exigiría repetir cuadros o ralentizar,
y eso cambia lo que se ve: es una transformación del contenido, no un ajuste de
duración. El plan avisa de que no alcanzó y quien llama decide qué hacer.
"""

from dataclasses import dataclass
from enum import StrEnum

from media_optimizer.core.scene import Scene

MINIMO_POR_ESCENA = 1.0

_MILISEGUNDOS = 1000
_NADA = 0


class TrimStrategy(StrEnum):
    """Cómo se reparte el recorte entre las escenas."""

    PROPORTIONAL = "proportional"
    DROP_TAIL = "drop_tail"


@dataclass(frozen=True, slots=True)
class TrimPlan:
    """Qué escenas se usan, con qué duración, y cuáles quedaron fuera."""

    scenes: tuple[Scene, ...]
    target_seconds: float
    strategy: TrimStrategy
    dropped: tuple[int, ...]

    @property
    def total_seconds(self) -> float:
        """Lo que suman de verdad las escenas conservadas."""
        milisegundos = sum(_a_milisegundos(escena.duration_seconds) for escena in self.scenes)
        return milisegundos / _MILISEGUNDOS

    @property
    def is_exact(self) -> bool:
        """Si se alcanzó la meta al milisegundo.

        Se calcula en vez de guardarse: no puede existir un plan que diga que
        cerró y no cierre.
        """
        return _a_milisegundos(self.total_seconds) == _a_milisegundos(self.target_seconds)


def trim_to_target(
    scenes: tuple[Scene, ...],
    target_seconds: float,
    *,
    strategy: TrimStrategy = TrimStrategy.PROPORTIONAL,
    min_scene_seconds: float = MINIMO_POR_ESCENA,
) -> TrimPlan:
    """Ajusta las escenas para que sumen exactamente la duración pedida.

    Si el material no llega a la meta se devuelve entero: alargarlo exigiría
    inventar contenido.

    Raises:
        ValueError: si la meta o el mínimo por escena no son positivos.
    """
    if target_seconds <= _NADA:
        msg = f"target_seconds debe ser mayor que cero, se recibió {target_seconds}"
        raise ValueError(msg)
    if min_scene_seconds <= _NADA:
        msg = f"min_scene_seconds debe ser mayor que cero, se recibió {min_scene_seconds}"
        raise ValueError(msg)

    meta = _a_milisegundos(target_seconds)
    disponible = sum(_a_milisegundos(escena.duration_seconds) for escena in scenes)
    if disponible <= meta:
        return TrimPlan(scenes, target_seconds, strategy, dropped=())

    minimo = _a_milisegundos(min_scene_seconds)
    if strategy is TrimStrategy.DROP_TAIL:
        conservadas = _quitando_del_final(scenes, meta, minimo)
    else:
        conservadas = _proporcional(scenes, meta, minimo)

    usados = {escena.index for escena in conservadas}
    descartadas = tuple(e.index for e in scenes if e.index not in usados)
    return TrimPlan(conservadas, target_seconds, strategy, dropped=descartadas)


def _proporcional(scenes: tuple[Scene, ...], meta: int, minimo: int) -> tuple[Scene, ...]:
    """Encoge todas por igual, apartando las que quedarían demasiado breves.

    Cada vez que una escena cae bajo el mínimo se descarta y se vuelve a repartir
    entre las que quedan. El conjunto se reduce en cada vuelta, así que termina.
    """
    candidatas = list(scenes)
    while candidatas:
        total = sum(_a_milisegundos(escena.duration_seconds) for escena in candidatas)
        repartos = [_a_milisegundos(e.duration_seconds) * meta // total for e in candidatas]
        if all(reparto >= minimo for reparto in repartos):
            return _con_duraciones(candidatas, _con_residuo(repartos, meta))
        candidatas = [
            escena
            for escena, reparto in zip(candidatas, repartos, strict=True)
            if reparto >= minimo
        ]
    return ()


def _quitando_del_final(scenes: tuple[Scene, ...], meta: int, minimo: int) -> tuple[Scene, ...]:
    """Conserva las primeras enteras y recorta la que cruza la meta."""
    conservadas: list[Scene] = []
    restante = meta
    for escena in scenes:
        duracion = _a_milisegundos(escena.duration_seconds)
        if restante <= _NADA:
            break
        if duracion <= restante:
            conservadas.append(escena)
            restante -= duracion
            continue
        if restante >= minimo:
            conservadas.append(_recortada(escena, restante))
        restante = _NADA
    return tuple(conservadas)


def _con_residuo(repartos: list[int], meta: int) -> list[int]:
    """Da el sobrante de la división a la última escena, para que la suma cierre."""
    ajustados = list(repartos)
    ajustados[-1] += meta - sum(ajustados)
    return ajustados


def _con_duraciones(scenes: list[Scene], duraciones: list[int]) -> tuple[Scene, ...]:
    return tuple(
        _recortada(escena, milisegundos)
        for escena, milisegundos in zip(scenes, duraciones, strict=True)
    )


def _recortada(scene: Scene, milisegundos: int) -> Scene:
    """La misma escena quedándose con su principio, hasta la duración pedida."""
    return Scene(
        index=scene.index,
        start_seconds=scene.start_seconds,
        end_seconds=scene.start_seconds + milisegundos / _MILISEGUNDOS,
    )


def _a_milisegundos(segundos: float) -> int:
    """Milisegundos enteros, que es donde la suma cierra sin arrastrar error."""
    return round(segundos * _MILISEGUNDOS)
