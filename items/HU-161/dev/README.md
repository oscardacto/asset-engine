# HU-161 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/core/errors.py` | Jerarquía: `MediaOptimizerError` (base de lo esperable) → `CorruptMediaError` (con `source: Path` + `reason: str` estructurados) e `InvalidInputError` (mensaje accionable). "Bug" queda fuera por diseño: los `ValueError` de los contratos NO heredan de la base |
| `src/media_optimizer/core/__init__.py` | Re-exporta los 3 errores (8 nombres públicos en `core/`) |
| `tests/core/test_errors.py` | 9 tests: jerarquía, contrato de captura del orquestador (la base atrapa corrupto+inválido y deja pasar bugs), causas estructuradas, capa secundaria |

Decisiones aplicadas de la spec: constructores permisivos (A-1 — una excepción debe ser
barata y segura de construir dentro de un `except`), sin subclases finas (A-2 — llegan
con HU-002/136 si las justifican).

Evidencia DEV (2026-07-26): **40 tests passed (9 nuevos) · cobertura `core/` 100%** ·
ruff check/format limpios · mypy estricto Success (5 archivos).
