"""Con qué número termina el programa, y qué significa cada uno.

En simple: al terminar, un programa de consola deja un número que dice cómo le
fue. Cero es "todo bien". El resto distingue entre "tú escribiste mal el comando",
"tu entrada no sirve" y "yo no pude terminar" — para que un script que encadene
comandos sepa si seguir o parar.

El caso interesante es ``PARTIAL``. El programa está hecho para que una foto
dañada se aparte y el lote continúe, así que **terminar con fallos parciales es lo
normal, no la excepción**. Sin un número propio habría que elegir entre mentir
—decir que todo fue bien ocultando doce fotos en cuarentena— o alarmar —decir que
falló cuando el resultado sirve—.
"""

from enum import IntEnum


class ExitCode(IntEnum):
    """Códigos con los que la CLI termina."""

    OK = 0
    FAILURE = 1
    USAGE = 2
    INVALID_INPUT = 3
    PARTIAL = 4
