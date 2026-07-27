# Entregables — HU-006

## Integración
| Merge | Repositorio | Rama | Descripción |
|-------|-------------|------|-------------|
| `d05acb4` | oscardacto/asset-engine | `feature/HU-006-hash-duplicados` → `develop` | Primer merge integrado por Claude bajo la delegación del 26-jul-2026 (CLAUDE.md, límites de autonomía): batería verificada en verde **sobre la rama ya fusionada** antes de publicar. Ratifica A-1 (SHA-256) y A-2 (duplicado = byte a byte) |

> Nota de proceso: hasta HU-002 la integración fue vía Pull Request en GitHub (#1–#10)
> aprobado por @oscardacto. Desde HU-006 el merge a `develop` lo ejecuta Claude y el gate
> humano pasa a `develop → main`.

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| N/A — solo lectura binaria de archivos | — | — | — |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

Batería ejecutada sobre `develop` con el merge ya aplicado (`d05acb4`), 2026-07-26:

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 Hash depende solo del contenido | mismo contenido como `a.jpg` y `sesion/copia_de_a.jpg` · dos contenidos distintos | hash igual · hash distinto | ✅ passed (2 tests) | pytest `TestHashDeContenido` |
| CA-2 Es SHA-256 de verdad | archivo vacío | `e3b0c442…b855` (vector conocido) | ✅ passed | pytest `TestHashDeContenido` |
| CA-3 Duplicados por contenido, no por nombre | `original.jpg` + `IMG (1).jpg` idénticos + `otra.jpg` distinta | un grupo con las dos copias | ✅ passed | pytest `TestAgrupamiento` |
| CA-4 Lote sin duplicados | tres contenidos distintos | resultado vacío | ✅ passed | pytest `TestAgrupamiento` |
| CA-5 Orden determinista | misma lista en orden normal e invertido | resultados idénticos; rutas ordenadas dentro del grupo | ✅ passed (2 tests) | pytest `TestAgrupamiento` |
| CA-6 Lectura por bloques | archivo de ~3 MB (mayor que el bloque de 1 MiB) | hash idéntico al de `hashlib` sobre el contenido completo | ✅ passed | pytest `TestLecturaPorBloques` |
| CA-7 Ilegible degrada con causa | ruta inexistente | `CorruptMediaError` con `source` y causa | ✅ passed | pytest `TestArchivoIlegible` |
| CA-8 No destructivo | bytes y `st_mtime_ns` antes/después | idénticos | ✅ passed | pytest `TestNoDestructivo` |
| CA-9 Cobertura ≥80% | `pytest --cov=media_optimizer.ingest` | ≥80% | ✅ **100%** (102/102 stmts) | log de cierre |
| CA-10 Batería completa | pytest · ruff check/format · mypy | todo exit 0 | ✅ 128 passed · limpio · Success (12 archivos) | log de cierre |
| CA-11 Trazabilidad | gate-log HU-006 | draft/gate_spec/dev | ✅ + qa/done de este cierre | gate-log.jsonl |

**Resultado: 11/11 criterios cumplidos · 0 fallidos · sin rework.**
Capa secundaria (etiquetada): dos archivos vacíos son duplicados entre sí, tres copias en un solo grupo, lote vacío sin grupos, inmutabilidad de `DuplicateGroup`.

## Commits relevantes
- `451585b` — HU-006 DRAFT+SPEC (93%, 0 bloqueantes)
- `162b283` — HU-006 DEV: `hashing.py` + tests (verde a la primera)
- `d05acb4` — merge a `develop`
