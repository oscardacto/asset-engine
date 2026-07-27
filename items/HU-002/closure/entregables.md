# Entregables — HU-002

## PRs mergeados
| PR # | Repositorio | Rama | Descripción |
|------|-------------|------|-------------|
| [#10](https://github.com/oscardacto/asset-engine/pull/10) | oscardacto/asset-engine | `feature/HU-002-formatos-imagen` → `develop` | Identificación por firma binaria + 18 tests. El merge ratifica A-1 (soportados = JPEG/PNG/WebP) y A-2 (HEIC/AVIF reconocidos pero no soportados) |

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| N/A — solo lectura de 16 bytes por archivo | — | — | — |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

Batería ejecutada sobre `develop` post-merge (2b4e736), 2026-07-26:

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 Contenido sobre extensión | JPEG real guardado como `foto.txt` · texto guardado como `documento.jpg` | `JPEG` · `None` | ✅ passed (2 tests) | pytest `TestContenidoSobreExtension` |
| CA-2 Formatos soportados | JPEG, PNG y WebP generados por el stack real | detectados y `is_supported_image` True | ✅ passed (parametrizado, 3 casos) | pytest `TestFormatosSoportados` |
| CA-3 Reconocido no soportado | cabeceras `ftypheic`, `ftypmif1`, `ftypavif` | `HEIC`/`HEIC`/`AVIF`, soportado False | ✅ passed (3 casos) | pytest `TestReconocidosNoSoportados` |
| CA-4 Desconocido sin excepción | bytes sin firma · archivo vacío · `ftypisom` (mp4) | `None` en los tres, sin lanzar | ✅ passed (3 tests) | pytest `TestDesconocidos` |
| CA-5 Ilegible degrada con causa | ruta inexistente | `CorruptMediaError` con `source` y causa en el mensaje | ✅ passed (verifica también el campo `source`) | pytest `TestArchivoIlegible` |
| CA-6 Firma ≠ integridad | cabecera JPEG válida + basura detrás | detecta `JPEG` (comportamiento deliberado) | ✅ passed | pytest `TestFirmaNoEsIntegridad` |
| CA-7 Coherencia con el stack | cada formato de `SUPPORTED_FORMATS` | cv2 lo codifica y decodifica de vuelta | ✅ passed (3 casos) | pytest `TestCoherenciaConElStack` |
| CA-8 No destructivo | bytes y `st_mtime_ns` antes/después | idénticos | ✅ passed | pytest `TestNoDestructivo` |
| CA-9 Cobertura ≥80% | `pytest --cov=media_optimizer.ingest` | ≥80% | ✅ **100%** (72/72 stmts) | log de cobertura |
| CA-10 Batería completa | pytest · ruff check/format · mypy | todo exit 0 | ✅ 113 passed · limpio · Success (11 archivos) | log de cierre |
| CA-11 Trazabilidad | gate-log HU-002 | draft/gate_spec/dev | ✅ + qa/done de este cierre | gate-log.jsonl |

**Resultado: 11/11 criterios cumplidos · 0 fallidos · sin rework.**
Capa secundaria (etiquetada): archivo más corto que la firma, RIFF que no es WebP (WAV), serialización plana del enum, inmutabilidad del conjunto soportado.

## Commits relevantes
- `efc2957` — HU-002 DRAFT+SPEC (92%, 0 bloqueantes) con verificación empírica del stack
- `85abf6e` — HU-002 DEV: `formats.py` + tests
- `2b4e736` — merge PR #10 a `develop`
