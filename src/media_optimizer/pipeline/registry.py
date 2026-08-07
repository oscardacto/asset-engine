"""Qué etapas y qué reportes existen. La lista vive aquí, no en la línea de comandos.

En simple: el programa hace su trabajo por etapas —leer la carpeta, analizar las
fotos, revelarlas, elegir las mejores, armar el reel— y produce reportes sobre lo
que hizo. Esta es la lista de unas y otros.

Está separada de la línea de comandos a propósito. Si cada etapa fuera un comando,
la interfaz crecería cada vez que el programa aprende a hacer algo nuevo, y en
poco tiempo habría veinte comandos que mantener. Así, en cambio, la interfaz tiene
tres verbos fijos y **añadir una etapa es añadir una línea a este archivo**.

Cada entrada declara qué es y qué hace. El código que la ejecuta llega con su
propio desarrollo; hasta entonces la etapa aparece en la ayuda y avisa con claridad
de que todavía no está disponible, en vez de fingir que no existe.

Si una etapa está disponible **no se declara aquí: se deriva** de que exista quien
la ejecute. Así no puede pasar que la lista diga "disponible" sin que el código
exista, ni lo contrario.
"""

from dataclasses import dataclass

from media_optimizer.pipeline.stages import available_stages

SECUENCIA_COMPLETA = "all"


@dataclass(frozen=True, slots=True)
class StageEntry:
    """Una etapa del pipeline: su nombre y qué hace."""

    name: str
    description: str

    @property
    def available(self) -> bool:
        """Si ya existe quien la ejecute en esta versión."""
        return self.name in available_stages()


@dataclass(frozen=True, slots=True)
class ReportEntry:
    """Un reporte sobre lo que el pipeline produjo."""

    name: str
    description: str

    @property
    def available(self) -> bool:
        """Si ya existe quien lo genere en esta versión."""
        return False


STAGES: tuple[StageEntry, ...] = (
    StageEntry("ingest", "Lee la carpeta de origen y arma el catálogo."),
    StageEntry("analyze", "Mide la calidad técnica de cada foto del catálogo."),
    StageEntry("develop", "Produce las versiones reveladas según el perfil."),
    StageEntry("select", "Elige y ordena las mejores para cada formato de salida."),
    StageEntry("reel", "Arma el vertical 9:16 a partir de los clips."),
    StageEntry(SECUENCIA_COMPLETA, "Ejecuta todas las etapas anteriores en orden."),
)

REPORTS: tuple[ReportEntry, ...] = (
    ReportEntry("inventory", "Qué hay en el lote: dimensiones, orientación y advertencias."),
    ReportEntry("analysis", "Calidad medida del lote, ordenada por puntaje."),
    ReportEntry("develop", "Antes y después del revelado."),
    ReportEntry("selection", "Qué quedó dentro y fuera de la selección, y por qué."),
    ReportEntry("reel", "Escenas usadas y descartadas del reel."),
    ReportEntry("run", "Resumen consolidado de la última ejecución."),
    ReportEntry("history", "Comparación entre lotes, para ver si el pipeline mejora."),
)


def stage_names() -> tuple[str, ...]:
    """Nombres de las etapas, en el orden en que se ejecutan."""
    return tuple(etapa.name for etapa in STAGES)


def report_names() -> tuple[str, ...]:
    """Nombres de los reportes disponibles."""
    return tuple(reporte.name for reporte in REPORTS)


def find_stage(name: str) -> StageEntry | None:
    """La etapa que se llama así, o ``None`` si no existe."""
    return next((etapa for etapa in STAGES if etapa.name == name), None)


def find_report(name: str) -> ReportEntry | None:
    """El reporte que se llama así, o ``None`` si no existe."""
    return next((reporte for reporte in REPORTS if reporte.name == name), None)
