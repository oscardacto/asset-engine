"""Contrato ``BusinessProfile``: la forma que tiene el criterio de un negocio.

En simple: el programa no sabe qué es un hospedaje ni qué es un bar. Sabe leer un
perfil que dice qué ambientes espera ver, en qué tamaños quiere las salidas, cuánto
pesa cada métrica al calificar una foto y a partir de qué valores algo se descarta.
Cambiar de negocio es cambiar ese perfil, no el código.

Aquí solo vive la **forma**. Los datos de un negocio concreto llegan en su archivo
de perfil, y leerlo es tarea de otra capa: este módulo no abre archivos.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType

_PESO_MINIMO = 0.0
_DIMENSION_MINIMA = 1


class OutputIntent(StrEnum):
    """Para qué se produce una salida.

    Es una lista cerrada a propósito: una intención existe porque hay una etapa
    del pipeline que sabe producirla. Si un perfil pudiera inventar intenciones,
    pediría salidas que nadie sabe generar.
    """

    COVER = "cover"
    FEED = "feed"
    STORY = "story"


@dataclass(frozen=True, slots=True)
class OutputFormat:
    """Un tamaño de salida: para qué es y cuántos píxeles mide.

    El aspecto no se declara, se deduce de las dimensiones: así no puede haber un
    perfil que diga "4:5" y traiga medidas que no lo son.
    """

    intent: OutputIntent
    width: int
    height: int

    def __post_init__(self) -> None:
        for nombre, valor in (("width", self.width), ("height", self.height)):
            if valor < _DIMENSION_MINIMA:
                msg = f"{nombre} debe ser >= {_DIMENSION_MINIMA} px, se recibió {valor}"
                raise ValueError(msg)

    @property
    def aspect_ratio(self) -> float:
        """Ancho dividido por alto. Un 4:5 da 0.8; un 9:16, 0.5625."""
        return self.width / self.height

    def accepts(self, width: int, height: int) -> bool:
        """Indica si una imagen de ese tamaño alcanza para llenar el formato."""
        return width >= self.width and height >= self.height


@dataclass(frozen=True, slots=True)
class ScoringWeights:
    """Cuánto pesa cada métrica al calificar, para una intención de salida.

    Los nombres de las métricas los pone el perfil, no este módulo: qué se mide y
    cuánto importa es criterio del negocio. Un peso de ``0.0`` es válido y
    significa "esta métrica no cuenta aquí".
    """

    intent: OutputIntent
    weights: Mapping[str, float] = field(hash=False)

    def __post_init__(self) -> None:
        normalizados: dict[str, float] = {}
        for metrica, peso in sorted(self.weights.items()):
            if not metrica.strip():
                msg = "toda métrica ponderada necesita un nombre no vacío"
                raise ValueError(msg)
            if not math.isfinite(peso) or peso < _PESO_MINIMO:
                msg = f"el peso de {metrica!r} debe ser un número finito >= 0, se recibió {peso!r}"
                raise ValueError(msg)
            normalizados[metrica] = peso
        object.__setattr__(self, "weights", MappingProxyType(normalizados))

    def weight_for(self, metric: str, default: float = 0.0) -> float:
        """Peso de una métrica; ``default`` si el perfil no la menciona."""
        return self.weights.get(metric, default)


@dataclass(frozen=True, slots=True)
class BusinessProfile:
    """El criterio de un negocio, como datos: ambientes, formatos, pesos y umbrales.

    Todas sus colecciones quedan ordenadas al construirse. Eso no es cosmético: el
    pipeline promete que la misma entrada produce siempre la misma salida, y
    recorrer un perfil en distinto orden bastaría para romperlo.

    Un valor imposible —nombre vacío, intención repetida, peso negativo— falla al
    construir, no más tarde. Traducir esos fallos a un mensaje que el dueño del
    perfil pueda arreglar es tarea de la capa que lo carga.
    """

    name: str
    version: str
    environments: tuple[str, ...] = ()
    formats: tuple[OutputFormat, ...] = ()
    scoring: tuple[ScoringWeights, ...] = ()
    thresholds: Mapping[str, float] = field(default_factory=dict, hash=False)

    def __post_init__(self) -> None:
        for campo, valor in (("name", self.name), ("version", self.version)):
            if not valor.strip():
                msg = f"{campo} del perfil no puede estar vacío"
                raise ValueError(msg)
        object.__setattr__(self, "environments", _ambientes_ordenados(self.environments))
        object.__setattr__(self, "formats", _por_intencion(self.formats, "formato"))
        object.__setattr__(self, "scoring", _por_intencion(self.scoring, "grupo de pesos"))
        object.__setattr__(self, "thresholds", _umbrales_ordenados(self.thresholds))

    def format_for(self, intent: OutputIntent) -> OutputFormat | None:
        """Formato de salida de esa intención, o ``None`` si el perfil no la produce."""
        return next((formato for formato in self.formats if formato.intent is intent), None)

    def weights_for(self, intent: OutputIntent) -> ScoringWeights:
        """Pesos de esa intención; un grupo vacío si el perfil no la califica."""
        return next(
            (pesos for pesos in self.scoring if pesos.intent is intent),
            ScoringWeights(intent=intent, weights={}),
        )

    def threshold(self, name: str, default: float | None = None) -> float | None:
        """Umbral técnico por nombre; ``default`` si el perfil no lo define."""
        return self.thresholds.get(name, default)


def _ambientes_ordenados(environments: tuple[str, ...]) -> tuple[str, ...]:
    vistos: set[str] = set()
    for ambiente in environments:
        if not ambiente.strip():
            msg = "los ambientes esperados no pueden estar vacíos"
            raise ValueError(msg)
        if ambiente in vistos:
            msg = f"el ambiente {ambiente!r} está repetido"
            raise ValueError(msg)
        vistos.add(ambiente)
    return tuple(sorted(environments))


def _por_intencion[T: OutputFormat | ScoringWeights](
    elementos: tuple[T, ...], etiqueta: str
) -> tuple[T, ...]:
    """Ordena por intención y rechaza duplicados: una intención, una respuesta."""
    intenciones = [elemento.intent for elemento in elementos]
    repetida = next((i for i in intenciones if intenciones.count(i) > 1), None)
    if repetida is not None:
        msg = f"hay más de un {etiqueta} para la intención {repetida.value!r}"
        raise ValueError(msg)
    return tuple(sorted(elementos, key=lambda elemento: elemento.intent.value))


def _umbrales_ordenados(thresholds: Mapping[str, float]) -> Mapping[str, float]:
    normalizados: dict[str, float] = {}
    for nombre, valor in sorted(thresholds.items()):
        if not nombre.strip():
            msg = "todo umbral necesita un nombre no vacío"
            raise ValueError(msg)
        if not math.isfinite(valor):
            msg = f"el umbral {nombre!r} debe ser un número finito, se recibió {valor!r}"
            raise ValueError(msg)
        normalizados[nombre] = valor
    return MappingProxyType(normalizados)
