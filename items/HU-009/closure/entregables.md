# Entregables — HU-009

## Integración
| Merge | Repositorio | Rama | Descripción |
|-------|-------------|------|-------------|
| `780f2b6` | oscardacto/asset-engine | `feature/HU-009-cuarentena` → `develop` | Triaje con causa + 15 tests. Integrado por Claude con batería verificada sobre la rama fusionada. Ratifica A-1 (cuarentena = registro, no movimiento) y A-2 (truncamiento por marca de cierre) |

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| N/A — el triaje solo lee cabecera y cola de cada archivo | — | — | — |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

Batería ejecutada sobre `develop` con el merge aplicado (`780f2b6`), 2026-07-26:

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 El lote continúa | foto válida + ruta inexistente + basura binaria | la válida aceptada, las otras apartadas, sin excepción | ✅ passed | pytest `TestElLoteContinua` |
| CA-2 Cada causa se distingue | ilegible, vacío, basura, HEIC, JPEG truncado | los 5 motivos correctos (comparación exacta del mapa completo) | ✅ passed | pytest `TestMotivosDistinguibles` |
| CA-3 Detalle accionable | archivo HEIC | el detalle nombra el formato concreto | ✅ passed | pytest `TestMotivosDistinguibles` |
| CA-4 Truncado sin decodificar | JPEG al 50% vs el mismo completo | el cortado apartado como `TRUNCATED`, el completo aceptado | ✅ passed | pytest `TestTruncamiento` |
| CA-5 Sin falsos positivos por relleno | JPEG válido + 16 bytes tras el cierre | aceptado | ✅ passed | pytest `TestTruncamiento` |
| CA-6 Particiones disjuntas y completas | lote mixto de 4 archivos | aceptados + apartados = 4, sin intersección | ✅ passed | pytest `TestRepartoCompleto` |
| CA-7 Determinismo | mismo lote en orden normal e invertido | resultados idénticos | ✅ passed | pytest `TestDeterminismo` |
| CA-8 No destructivo | bytes y `st_mtime_ns` de 2 archivos antes/después | idénticos | ✅ passed | pytest `TestNoDestructivo` |
| CA-9 Cobertura ≥80% | `pytest --cov=media_optimizer.ingest` | ≥80% | ✅ **100%** (172/172 stmts) | log de cierre |
| CA-10 Batería completa | pytest · ruff check/format · mypy | todo exit 0 | ✅ 143 passed · limpio · Success (13 archivos) | log de cierre |
| CA-11 Trazabilidad | gate-log HU-009 | draft/gate_spec/dev | ✅ + qa/done de este cierre | gate-log.jsonl |

**Resultado: 11/11 criterios cumplidos · 0 fallidos · sin rework.**
Capa secundaria (etiquetada): lote vacío, PNG y WebP completos aceptados, PNG y WebP truncados apartados (parametrizados), serialización plana del enum, inmutabilidad del resultado.

## Commits relevantes
- `113c063` — HU-009 DRAFT+SPEC (90%, 0 bloqueantes)
- `74fcf51` — HU-009 DEV: `quarantine.py` + tests
- `780f2b6` — merge a `develop`
