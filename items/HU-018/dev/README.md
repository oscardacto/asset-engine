# HU-018 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/pipeline/reports.py` | `generate_report` + generador de `inventory` (markdown y texto) |
| `src/media_optimizer/pipeline/registry.py` | `ReportEntry.available` derivado del generador |
| `src/media_optimizer/cli/commands/report.py` | Invoca la generación real; consola + archivo |
| `tests/pipeline/test_reports.py` | 13 tests |

**El reporte es salida persistida**, así que la promesa byte a byte lo cubre: sin fecha ni
hora, datos ya ordenados del catálogo, y test de que dos generaciones producen los mismos
bytes. Un reporte **no calcula nada**: si falta el catálogo dice qué etapa ejecutar.

**Simetría con las etapas:** `reports.py` es a `report` lo que `stages.py` a `run` — mismo
patrón de registro con disponibilidad derivada, misma verificación.

**Validado con el lote real:** las 102 fotos del cliente en tabla, 7 en cuarentena con
causa, formato del Maestro §8.2.

Evidencia DEV: **491 tests (13 nuevos) · `reports.py` 100% · `commands/report.py` 100%** ·
ruff y mypy limpios.
