"""Selección: de las fotos calificadas a la portada, la galería y cada formato.

En simple: ya sabemos qué tan buena es cada foto; aquí se decide cuáles se usan y
en qué orden. La portada sale de las mejores publicables que llenan el formato de
portada; la galería arranca con el gancho —la mejor foto— y alterna orientaciones
para dar ritmo visual; y cada formato de salida recibe solo fotos que de verdad lo
llenan: una foto corta de píxeles para story no entra en story, aunque sea bella.

Todo criterio numérico llega como datos (pesos, cuántas candidatas), y el orden es
reproducible hasta el último desempate: a igual score decide el nombre, así dos
corridas dan siempre la misma selección.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from media_optimizer.core import Verdict

_FLAG_BAJO_NATIVO = "below_native_"


@dataclass(frozen=True, slots=True)
class RankedAsset:
    """Una foto ya calificada, con lo necesario para seleccionar."""

    content_hash: str
    source: str
    score: float
    verdict: Verdict
    flags: tuple[str, ...]
    width: int
    height: int

    def eligible_for(self, intent: str) -> bool:
        """Si la foto llena el formato de esa intención (no está bajo el nativo)."""
        return f"{_FLAG_BAJO_NATIVO}{intent}" not in self.flags

    @property
    def is_vertical(self) -> bool:
        return self.height > self.width


def global_score(metrics: Mapping[str, float], weights: Mapping[str, float]) -> float:
    """Combinación ponderada de métricas según los pesos del perfil.

    Normaliza por la suma de pesos: ajustar un peso no obliga a recalcular los
    demás (la decisión que HU-160 dejó documentada).
    """
    total = sum(weights.values())
    if total <= 0:
        return 0.0
    return sum(metrics.get(nombre, 0.0) * peso for nombre, peso in weights.items()) / total


def rank(assets: tuple[RankedAsset, ...]) -> tuple[RankedAsset, ...]:
    """Ordena por score descendente con desempate estable por nombre."""
    return tuple(sorted(assets, key=lambda a: (-a.score, a.source)))


def cover_candidates(assets: tuple[RankedAsset, ...], top: int) -> tuple[RankedAsset, ...]:
    """Las mejores publicables que llenan el formato de portada."""
    elegibles = tuple(
        a for a in rank(assets) if a.verdict is Verdict.PUBLISHABLE and a.eligible_for("cover")
    )
    return elegibles[:top]


def gallery_order(assets: tuple[RankedAsset, ...]) -> tuple[RankedAsset, ...]:
    """El orden de la galería: gancho primero, luego alternando orientación.

    La plantilla narrativa por ambientes (gancho → espacio → edificio → ubicación)
    entra cuando exista el etiquetado de ambientes; mientras tanto el ritmo lo da
    la alternancia visual, y el arranque siempre es la mejor foto del lote.
    """
    usables = [a for a in rank(assets) if a.verdict is not Verdict.DISCARD]
    if not usables:
        return ()
    galeria = [usables.pop(0)]
    while usables:
        anterior = galeria[-1]
        indice = next(
            (i for i, a in enumerate(usables) if a.is_vertical != anterior.is_vertical), 0
        )
        galeria.append(usables.pop(indice))
    return tuple(galeria)


def select_by_format(
    assets: tuple[RankedAsset, ...], intents: tuple[str, ...]
) -> dict[str, tuple[RankedAsset, ...]]:
    """Para cada intención de salida, las fotos que la llenan, ya ordenadas.

    Los descartes no entran nunca; el material de apoyo sí, detrás de las
    publicables por su propio score.
    """
    ordenadas = tuple(a for a in rank(assets) if a.verdict is not Verdict.DISCARD)
    return {
        intencion: tuple(a for a in ordenadas if a.eligible_for(intencion)) for intencion in intents
    }
