"""Plantillas narrativas: el guion del reel, escrito como datos y no como código.

En simple: un reel no es una pila de clips, es un relato — se abre con algo que
enganche, se muestra el espacio, se cierra con un detalle. Ese guion lo escribe
el negocio en su perfil: cuántos tramos, qué ambiente va en cada uno y cuánto
dura. Aquí solo vive la **forma** del guion y cómo se le asignan los clips.

Los tramos no están escritos en el código a propósito. Un hospedaje querrá abrir
con la fachada y un restaurante con el plato: si los nombres vivieran aquí,
cambiar de negocio exigiría cambiar el programa. Son texto libre del perfil.

Cuando falta material para un tramo, **el hueco se conserva** en vez de rellenarse
con cualquier clip: saber qué falta grabar es más útil que un reel completo con un
tramo que no corresponde.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from media_optimizer.core import InvalidInputError
from media_optimizer.ranking import RankedAsset

_DURACION_MINIMA = 0.1
_DURACION_MAXIMA = 60.0


@dataclass(frozen=True, slots=True)
class NarrativeSlot:
    """Un tramo del guion: qué ambiente espera y cuánto dura."""

    name: str
    duration_seconds: float
    setting: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "todo tramo del guion necesita un nombre no vacío"
            raise ValueError(msg)
        if not _DURACION_MINIMA <= self.duration_seconds <= _DURACION_MAXIMA:
            msg = (
                f"la duración de '{self.name}' debe estar entre {_DURACION_MINIMA} y "
                f"{_DURACION_MAXIMA} s, se recibió {self.duration_seconds}"
            )
            raise ValueError(msg)

    @property
    def accepts_any_setting(self) -> bool:
        """Si el tramo no exige un ambiente concreto."""
        return self.setting is None


@dataclass(frozen=True, slots=True)
class ReelTemplate:
    """El guion completo: los tramos en su orden exacto.

    No conoce ningún archivo ni ningún lote: sirve igual para todos los lotes del
    mismo negocio, que es lo que la vuelve reutilizable.
    """

    name: str
    slots: tuple[NarrativeSlot, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "la plantilla necesita un nombre no vacío"
            raise ValueError(msg)
        if not self.slots:
            msg = f"la plantilla '{self.name}' no tiene ningún tramo"
            raise ValueError(msg)
        nombres = [tramo.name for tramo in self.slots]
        repetido = next((n for n in nombres if nombres.count(n) > 1), None)
        if repetido is not None:
            msg = f"el tramo '{repetido}' está repetido en la plantilla '{self.name}'"
            raise ValueError(msg)

    @property
    def total_duration_seconds(self) -> float:
        """Cuánto dura el reel si todos los tramos se llenan."""
        return round(sum(tramo.duration_seconds for tramo in self.slots), 3)

    @property
    def expected_settings(self) -> tuple[str, ...]:
        """Los ambientes que el guion espera, ordenados y sin repetir."""
        return tuple(sorted({t.setting for t in self.slots if t.setting is not None}))


def template_from_data(data: Mapping[str, Any]) -> ReelTemplate:
    """Construye una plantilla desde los datos del perfil, validándolos como no confiables.

    Raises:
        InvalidInputError: si al guion le falta un campo o trae un valor imposible.
    """
    try:
        tramos = tuple(
            NarrativeSlot(
                name=str(tramo["name"]),
                duration_seconds=float(tramo["duration_seconds"]),
                setting=(str(tramo["setting"]) if tramo.get("setting") is not None else None),
            )
            for tramo in data["slots"]
        )
        return ReelTemplate(name=str(data["name"]), slots=tramos)
    except (KeyError, TypeError) as error:
        msg = f"el guion del reel está incompleto: falta {error}"
        raise InvalidInputError(msg) from error
    except ValueError as error:
        msg = f"el guion del reel tiene un valor inválido: {error}"
        raise InvalidInputError(msg) from error


@dataclass(frozen=True, slots=True)
class SlotAssignment:
    """Qué clip quedó en un tramo — o el hueco, si no había material."""

    slot: NarrativeSlot
    asset: RankedAsset | None

    @property
    def is_gap(self) -> bool:
        """Si el tramo quedó sin llenar por falta de material."""
        return self.asset is None


@dataclass(frozen=True, slots=True)
class Timeline:
    """El guion ya poblado: qué se ve, en qué orden y qué falta grabar."""

    template_name: str
    assignments: tuple[SlotAssignment, ...]

    @property
    def gaps(self) -> tuple[str, ...]:
        """Los tramos que quedaron vacíos: exactamente lo que falta grabar."""
        return tuple(a.slot.name for a in self.assignments if a.is_gap)

    @property
    def is_complete(self) -> bool:
        """Si todos los tramos encontraron material."""
        return not self.gaps

    @property
    def duration_seconds(self) -> float:
        """Cuánto dura el reel con lo que sí se llenó."""
        return round(sum(a.slot.duration_seconds for a in self.assignments if not a.is_gap), 3)


def assign_slots(
    template: ReelTemplate,
    candidates: Sequence[RankedAsset],
    settings: Mapping[str, str] | None = None,
) -> Timeline:
    """Reparte los mejores clips entre los tramos del guion, sin repetir ninguno.

    Un tramo que pide un ambiente concreto solo acepta clips etiquetados con ese
    ambiente; uno que no lo pide toma el mejor libre. Los clips llegan ya
    ordenados por calidad, así que el reparto es el mismo en cada corrida.

    Mientras nadie haya etiquetado los ambientes, los tramos que exigen uno quedan
    como huecos — el guion dice qué falta en vez de inventarlo.
    """
    etiquetas = settings or {}
    disponibles = list(candidates)
    reparto: list[SlotAssignment] = []
    for tramo in template.slots:
        elegido = _mejor_para(tramo, disponibles, etiquetas)
        if elegido is not None:
            disponibles.remove(elegido)
        reparto.append(SlotAssignment(slot=tramo, asset=elegido))
    return Timeline(template_name=template.name, assignments=tuple(reparto))


def _mejor_para(
    tramo: NarrativeSlot,
    disponibles: Sequence[RankedAsset],
    etiquetas: Mapping[str, str],
) -> RankedAsset | None:
    """El primer clip libre que sirve para el tramo, o ``None`` si no hay ninguno."""
    if tramo.accepts_any_setting:
        return disponibles[0] if disponibles else None
    return next(
        (clip for clip in disponibles if etiquetas.get(clip.content_hash) == tramo.setting),
        None,
    )
