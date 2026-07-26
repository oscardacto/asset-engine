"""Errores del dominio: distinguen archivo dañado, entrada inválida y bug.

En simple: hay tres formas de fallar. El archivo está dañado → se aparta con su
causa y el lote sigue. La entrada no sirve → se le explica al usuario qué
corregir. Hay un bug del programa → revienta con la excepción estándar de
Python, sin disfraz. Solo las dos primeras viven aquí: el pipeline captura
``MediaOptimizerError`` y deja pasar todo lo demás — envolver un bug en un
error del dominio lo escondería en el resumen de fallos del lote.
"""

from pathlib import Path


class MediaOptimizerError(Exception):
    """Base de todos los errores esperables del dominio."""


class CorruptMediaError(MediaOptimizerError):
    """El archivo no se puede leer o decodificar: se aparta llevando su causa."""

    def __init__(self, source: Path, reason: str) -> None:
        self.source = source
        self.reason = reason
        super().__init__(f"medio corrupto en '{source}': {reason}")


class InvalidInputError(MediaOptimizerError):
    """La entrada se pudo leer pero no sirve: el mensaje dice qué corregir."""
