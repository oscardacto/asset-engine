"""Lo que hace que dos ejecuciones iguales produzcan exactamente lo mismo.

En simple: el programa promete que si le das la misma carpeta dos veces, te
devuelve lo mismo hasta el último byte. Eso no sale gratis — hay dos formas
silenciosas de romperlo, y las dos se midieron en este proyecto:

**Un conjunto se recorre en distinto orden cada vez que arranca el programa.**
Python mezcla internamente sus tablas con un número que cambia en cada ejecución,
así que el mismo conjunto de etiquetas sale en otro orden cada vez. Por eso aquí
nada que llegue a una salida se guarda en un conjunto.

**El mismo nombre de archivo puede llegar escrito de dos maneras.** ``café.jpg``
se puede representar con la ``é`` entera, o con una ``e`` seguida de una tilde
suelta: dos secuencias de bytes distintas para el mismo nombre visible. macOS
entrega una y Windows la otra, así que la misma carpeta ordenada en dos máquinas
daría dos órdenes. Aquí todo texto se lleva primero a una forma única.
"""

import unicodedata
from collections.abc import Callable, Iterable
from typing import Final, Literal

FORMA_CANONICA: Final[Literal["NFC"]] = "NFC"


def stable_text(value: str) -> str:
    """Forma única de un texto, para que dos escrituras del mismo nombre coincidan."""
    return unicodedata.normalize(FORMA_CANONICA, value)


def stable_order(items: Iterable[str]) -> tuple[str, ...]:
    """Ordena textos igual en cualquier plataforma, sin duplicados de representación."""
    return tuple(sorted(stable_text(item) for item in items))


def stable_order_by[T](items: Iterable[T], key: Callable[[T], str]) -> tuple[T, ...]:
    """Ordena objetos por una clave de texto, con la misma garantía que ``stable_order``."""
    return tuple(sorted(items, key=lambda item: stable_text(key(item))))


def stable_unique(items: Iterable[str]) -> tuple[str, ...]:
    """Los textos distintos, ordenados: lo que aporta un conjunto, pero reproducible."""
    return tuple(sorted({stable_text(item) for item in items}))
