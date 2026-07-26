# HU-159 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/core/transform.py` | `Transform` declarativo (nombre + params escalares congelados con claves ordenadas, copia defensiva, anti-NaN) + `TransformHistory` (secuencia posicional inmutable; `append` puro que devuelve historial nuevo) + alias `ParamValue` |
| `src/media_optimizer/core/__init__.py` | Re-exporta los 3 nombres (11 públicos en `core/`) |
| `tests/core/test_transform.py` | 17 tests por comportamiento: declaración, inmutabilidad profunda, invariantes, historial auditable, igualdad, determinismo + capa secundaria (bool/int exentos del filtro de floats, retoque duplicado legítimo) |

Decisiones aplicadas de la spec: nombres de transform como string libre (A-1 — conjunto
abierto, el despachador de HU-056 valida), params escalares planos (A-2), historial como
contrato propio con `append` puro (A-3).

Corrección en DEV: 1 línea de test >100 columnas reformateada (detectada por ruff antes
del commit — la batería local hace su trabajo).

Evidencia DEV (2026-07-26): **57 tests passed (17 nuevos) · cobertura `core/` 100%**
(110/110 stmts) · ruff check/format limpios · mypy estricto Success (6 archivos).
