# Entregables — HU-161

## PRs mergeados
| PR # | Repositorio | Rama | Descripción |
|------|-------------|------|-------------|
| [#6](https://github.com/oscardacto/asset-engine/pull/6) | oscardacto/asset-engine | `feature/HU-161-excepciones-dominio` → `develop` | Jerarquía de excepciones del dominio + 9 tests. El merge ratifica A-1 (constructores permisivos) |

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| N/A — dominio puro | — | — | — |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

Batería ejecutada sobre `develop` post-merge (a799b2d), 2026-07-26:

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 Jerarquía correcta | `TestJerarquia` (2 tests) | ambas heredan de la base; base es Exception | ✅ passed | pytest |
| CA-2 Contrato de captura | `TestContratoDeCaptura` — corrupto/inválido capturados por la base; ValueError pasa de largo | la base no atrapa bugs | ✅ passed (2 tests) | pytest |
| CA-3 Corrupto con causa estructurada | `TestArchivoDanado` — source+reason como campos y en `str(e)` | expone y formatea ambos | ✅ passed (2 tests) | pytest |
| CA-4 Inválido accionable | `TestEntradaInvalida` — mensaje tal cual | `str(e)` == mensaje | ✅ passed | pytest |
| CA-5 Pureza y tipado | imports + mypy estricto | solo stdlib (`pathlib`); exit 0 | ✅ mypy Success (5 archivos) | código + log |
| CA-6 Cobertura ≥95% | `pytest --cov=media_optimizer.core` | ≥95% | ✅ **100%** (76/76 stmts) | log |
| CA-7 Batería completa | pytest · ruff check/format · mypy | todo exit 0 | ✅ 40 passed · limpio · Success | log |
| CA-8 Trazabilidad | gate-log HU-161 | draft/gate_spec/dev | ✅ + qa/done de este cierre | gate-log.jsonl |

**Resultado: 8/8 criterios cumplidos · 0 fallidos · sin rework.**
Capa secundaria (etiquetada): captura por tipo específico; `KeyboardInterrupt` fuera del dominio.

## Commits relevantes
- `ed9629c` — HU-161 DRAFT+SPEC (93%, 0 bloqueantes)
- `97bdc40` — HU-161 DEV: errors.py + tests
- `a799b2d` — merge PR #6 a `develop`
