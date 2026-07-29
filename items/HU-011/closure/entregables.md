# Entregables — HU-011

## Integración
| Merge | Repositorio | Rama | Descripción |
|-------|-------------|------|-------------|
| `f550531` | oscardacto/asset-engine | `feature/HU-011-limites-dimensiones` → `develop` | Lectura de dimensiones sin decodificar + causa `TOO_LARGE`. Integrado por Claude con batería verificada sobre la rama fusionada. Ratifica A-1 (umbrales 1 GiB / 65.535 px) y A-2 (ilegible ⇒ se acepta) |

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| N/A — solo lectura de cabecera | — | — | — |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

Batería ejecutada sobre `develop` con el merge aplicado (`f550531`), 2026-07-26:

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 Dimensiones en los 3 formatos | imagen 96×48 en JPEG, PNG y WebP (asimétrica a propósito) | 96×48 en los tres | ✅ passed (parametrizado) + variantes VP8X y VP8 con pérdida | pytest `TestDimensionesPorFormato` |
| CA-2 Se lee sin decodificar | cabecera PNG que declara 60.000×60.000 en un archivo de <100 bytes | se obtienen las dimensiones y se aparta | ✅ passed (el test verifica que el archivo pesa <100 bytes) | pytest `TestRechazoDeImagenesBomba` |
| CA-3 Bomba apartada con causa | bomba + foto normal en el mismo lote | foto aceptada, bomba `TOO_LARGE` con memoria y máximo en el detalle | ✅ passed (2 tests) | pytest `TestRechazoDeImagenesBomba` |
| CA-4 Foto legítima de alta resolución | cabecera PNG de 16.320×12.240 (≈200 MP, equipo de referencia) | aceptada | ✅ passed | pytest `TestFotosLegitimasDeAltaResolucion` |
| CA-5 Límite por lado | 70.000×2 px (pocos píxeles totales) | apartada por lado, con el máximo en el detalle | ✅ passed | pytest `TestRechazoDeImagenesBomba` |
| CA-6 Ilegible no descarta | JPEG válido en firma y cierre pero sin marcador de medidas | `read_image_size` → `None` y el triaje lo acepta | ✅ passed | pytest `TestDimensionesIlegibles` |
| CA-7 Causas anteriores intactas | los 15 tests de HU-009 | siguen pasando sin cambios | ✅ passed (suite completa verde) | pytest `tests/ingest/test_quarantine.py` |
| CA-8 No destructivo | bytes y `mtime` | idénticos (heredado del triaje, verificado en HU-009) | ✅ passed | pytest `TestNoDestructivo` |
| CA-9 Cobertura ≥80% | `pytest --cov=media_optimizer.ingest` | ≥80% | ✅ **100%** (287/287 stmts) | log de cierre |
| CA-10 Batería completa | pytest · ruff check/format · mypy | todo exit 0 | ✅ 167 passed · limpio · Success (14 archivos) | log de cierre |
| CA-11 Trazabilidad | gate-log HU-011 | draft/gate_spec/dev | ✅ + qa/done de este cierre | gate-log.jsonl |

**Resultado: 11/11 criterios cumplidos · 0 fallidos · sin rework.**
Capa secundaria (etiquetada): dimensiones cero tratadas como ilegibles, lado justo en el límite aceptado, JPEG con relleno `FF` antes del marcador, inmutabilidad de `ImageSize`.

## Commits relevantes
- `6e1e6f8` — HU-011 DRAFT+SPEC (90%, 0 bloqueantes) con verificación empírica de cabeceras
- `9ee5591` — HU-011 DEV: `dimensions.py` + causa `TOO_LARGE` + tests
- `f550531` — merge a `develop`
