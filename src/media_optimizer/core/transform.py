"""Contratos ``Transform`` y ``TransformHistory``: qué se le hizo a un medio y en qué orden.

En simple: cada retoque (recorte, contraste, balance de blancos…) se anota como
una tarjeta con su nombre y sus parámetros, y el historial es la lista ordenada
de esas tarjetas — la prueba auditable de cómo se llegó del original a la
salida, sin tocar jamás el original.
"""

import math
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Self

ParamValue = float | int | str | bool


@dataclass(frozen=True, slots=True)
class Transform:
    """Retoque declarado: nombre de la operación y sus parámetros.

    No ejecuta nada — solo describe. Los parámetros se copian a un mapping de
    solo lectura con claves ordenadas: el transform no cambia aunque el llamador
    mute su dict original. Nombres vacíos o floats no finitos (NaN/inf) fallan
    de inmediato con ``ValueError``.
    """

    name: str
    params: Mapping[str, ParamValue] = field(hash=False)

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "todo transform necesita un nombre no vacío"
            raise ValueError(msg)
        normalized: dict[str, ParamValue] = {}
        for key, value in sorted(self.params.items()):
            if not key.strip():
                msg = f"el transform {self.name!r} tiene un parámetro sin nombre"
                raise ValueError(msg)
            if isinstance(value, float) and not math.isfinite(value):
                msg = f"el parámetro {key!r} de {self.name!r} debe ser finito, se recibió {value!r}"
                raise ValueError(msg)
            normalized[key] = value
        object.__setattr__(self, "params", MappingProxyType(normalized))


@dataclass(frozen=True, slots=True)
class TransformHistory:
    """Secuencia inmutable de retoques en su orden exacto de aplicación.

    ``append`` no modifica nada: devuelve un historial nuevo con el paso al
    final, así cada versión anterior sigue siendo evidencia intacta.
    """

    steps: tuple[Transform, ...] = ()

    def append(self, transform: Transform) -> Self:
        """Devuelve un historial nuevo con el retoque agregado al final."""
        return type(self)(steps=(*self.steps, transform))

    def __len__(self) -> int:
        return len(self.steps)

    def __iter__(self) -> Iterator[Transform]:
        return iter(self.steps)
