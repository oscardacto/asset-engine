"""Línea de comandos: traduce lo que escribes en la terminal a trabajo del pipeline.

Es una capa de traducción y nada más — ninguna decisión sobre los medios se toma
aquí. Son tres comandos: hacer el trabajo (``run``), leer lo que salió
(``report``) y corregir a mano lo que la máquina propuso (``label``).

El punto de entrada vive en ``media_optimizer.cli.main``. No se reexporta aquí a
propósito: hacerlo taparía el módulo con la función del mismo nombre, y quien
quisiera el módulo se encontraría con la función sin entender por qué.
"""

from media_optimizer.cli.exit_codes import ExitCode

__all__ = ["ExitCode"]
