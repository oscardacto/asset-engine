"""Orquestación del pipeline: qué etapas existen y en qué orden se ejecutan."""

from media_optimizer.pipeline.registry import (
    REPORTS,
    SECUENCIA_COMPLETA,
    STAGES,
    ReportEntry,
    StageEntry,
    find_report,
    find_stage,
    report_names,
    stage_names,
)

__all__ = [
    "REPORTS",
    "SECUENCIA_COMPLETA",
    "STAGES",
    "ReportEntry",
    "StageEntry",
    "find_report",
    "find_stage",
    "report_names",
    "stage_names",
]
