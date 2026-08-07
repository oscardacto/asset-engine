"""Lo que el programa escribe en pantalla para que lo lea una persona.

En simple: el rastro estructurado (una línea JSON por evento) sirve para
diagnosticar y para filtrar con herramientas; esto es lo otro — las frases que lee
quien está ejecutando el comando. Son cosas distintas y por eso van por caminos
distintos: los avisos normales a la salida estándar, los fallos a la de errores.

Recibe los flujos de escritura en vez de tomarlos por su cuenta, para que las
pruebas puedan leer exactamente lo que se mostró.
"""

import sys
from dataclasses import dataclass, field
from typing import IO


def _salida_estandar() -> IO[str]:
    return sys.stdout


def _salida_de_errores() -> IO[str]:
    return sys.stderr


@dataclass(frozen=True, slots=True)
class Console:
    """Escribe mensajes para la persona que ejecuta el comando."""

    out: IO[str] = field(default_factory=_salida_estandar)
    err: IO[str] = field(default_factory=_salida_de_errores)
    quiet: bool = False

    def say(self, message: str) -> None:
        """Informa algo. Con ``--quiet`` no se escribe."""
        if not self.quiet:
            self.out.write(f"{message}\n")

    def fail(self, message: str) -> None:
        """Comunica un fallo. Se escribe siempre, aunque se haya pedido silencio."""
        self.err.write(f"{message}\n")
