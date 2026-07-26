# HU-158 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/core/quality_report.py` | Contrato `QualityReport` (frozen, slots) + enum `Verdict` (publishable/support/discard); métricas congeladas como mapping de solo lectura con claves ordenadas (copia defensiva); invariantes fail-fast: sin NaN/±inf, sin nombres ni flags vacíos |
| `src/media_optimizer/core/__init__.py` | Re-exporta `QualityReport` y `Verdict` |
| `tests/core/test_quality_report.py` | 14 tests organizados por comportamiento (construcción, inmutabilidad profunda, invariantes, veredicto cerrado, determinismo de iteración) + capa secundaria |

Decisiones aplicadas de la spec: reporte autónomo sin referencia al asset (A-1 — el
catálogo asocia), veredicto requerido (A-2), hash del reporte excluye las métricas
(mapping no hashable) manteniendo la consistencia igualdad⇒hash.

Evidencia DEV (2026-07-26): **31 tests passed (14 nuevos) · cobertura `core/` 100%** ·
ruff check/format limpios · mypy estricto Success (4 archivos).
