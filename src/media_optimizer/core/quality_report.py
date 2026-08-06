"""Contrato ``QualityReport``: el resultado del análisis de calidad de un medio.

En simple: la boleta de calificaciones de una foto o un video — números medidos
(métricas), advertencias encontradas (flags) y un veredicto final: publicable,
de apoyo o descartar.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType

from media_optimizer.core.determinism import stable_unique


class Verdict(StrEnum):
    """Destino técnico de un medio tras su análisis de calidad."""

    PUBLISHABLE = "publishable"
    SUPPORT = "support"
    DISCARD = "discard"


@dataclass(frozen=True, slots=True)
class QualityReport:
    """Boleta inmutable de calidad: métricas numéricas, flags de advertencia y veredicto.

    Las métricas se copian a un mapping de solo lectura con claves ordenadas: el
    reporte no cambia aunque el llamador mute su dict original, y siempre itera
    en el mismo orden. Valores no finitos (NaN/inf), nombres de métrica vacíos o
    flags vacíos fallan de inmediato con ``ValueError``.

    Los flags se guardan ordenados y sin repetir. Un conjunto habría sido el tipo
    natural, pero se recorre en distinto orden en cada ejecución del programa, y
    estos flags acaban escritos en un reporte que se compara byte a byte.
    """

    metrics: Mapping[str, float] = field(hash=False)
    flags: tuple[str, ...]
    verdict: Verdict

    def __post_init__(self) -> None:
        normalized: dict[str, float] = {}
        for name, value in sorted(self.metrics.items()):
            if not name.strip():
                msg = "toda métrica necesita un nombre no vacío"
                raise ValueError(msg)
            if not math.isfinite(value):
                msg = f"la métrica {name!r} debe ser un número finito, se recibió {value!r}"
                raise ValueError(msg)
            normalized[name] = value
        object.__setattr__(self, "metrics", MappingProxyType(normalized))

        for flag in self.flags:
            if not flag.strip():
                msg = "los flags no pueden estar vacíos"
                raise ValueError(msg)
        object.__setattr__(self, "flags", stable_unique(self.flags))
