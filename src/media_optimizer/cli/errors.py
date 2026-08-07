"""Convierte un fallo en algo que la persona pueda leer y arreglar.

En simple: cuando algo sale mal hay dos casos muy distintos. Si el problema es de
tu material o de tu configuración —una carpeta vacía, un perfil mal escrito, una
foto ilegible— verás una frase que dice qué corregir. Si el problema es un defecto
del programa, verás la traza completa del error, sin adornos.

Esa diferencia es deliberada. Disfrazar un defecto del programa de "error
esperable" lo escondería entre los avisos normales del lote, y nadie lo arreglaría
nunca.
"""

from media_optimizer.cli.exit_codes import ExitCode
from media_optimizer.core.errors import CorruptMediaError, InvalidInputError, MediaOptimizerError


def translate(error: MediaOptimizerError) -> tuple[str, ExitCode]:
    """Mensaje para la persona y código de salida que le corresponde al fallo.

    Solo entiende de fallos esperables. Cualquier otra excepción no pasa por aquí:
    se propaga con su traza, porque es un defecto del programa.
    """
    if isinstance(error, InvalidInputError):
        return str(error), ExitCode.INVALID_INPUT
    if isinstance(error, CorruptMediaError):
        return str(error), ExitCode.PARTIAL
    return str(error), ExitCode.FAILURE
