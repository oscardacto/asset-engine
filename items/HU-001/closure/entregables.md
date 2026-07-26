# Entregables — HU-001

## PRs mergeados
| PR # | Repositorio | Rama | Descripción |
|------|-------------|------|-------------|
| [#9](https://github.com/oscardacto/asset-engine/pull/9) | oscardacto/asset-engine | `feature/HU-001-escaneo-determinista` → `develop` | Escaneo determinista + 15 tests. El merge **ratifica el módulo `ingest/`** (P-1/A-1) y las asunciones A-2…A-5 |

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| N/A — el escaneo solo lee directorios; los tests trabajan en `tmp_path` | — | — | — |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

Batería ejecutada sobre `develop` post-merge (bf36345), 2026-07-26:

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 Orden determinista | archivos creados en orden `c`, `a`, `b` · dos escaneos seguidos | orden `a`, `b`, `c` · resultados idénticos | ✅ passed (2 tests) | pytest `TestOrdenDeterminista` |
| CA-2 Recursividad | `raiz/foto1.jpg` + `raiz/sesion/foto2.jpg` | ambos con default; solo el primero con `recursive=False` | ✅ passed (2 tests) | pytest `TestRecursividad` |
| CA-3 Sin filtrar por extensión | `foto.jpg`, `documento.txt`, `sin_extension` | los tres presentes | ✅ passed | pytest `TestQueSeIncluye` |
| CA-4 Omite directorios y ocultos | subdirectorio, `.oculta.jpg`, `.cache/interna.jpg` | solo el archivo visible | ✅ passed | pytest `TestQueSeIncluye` |
| CA-5 Carpeta vacía | directorio sin contenido | tupla vacía, sin excepción | ✅ passed | pytest `TestQueSeIncluye` |
| CA-6 Entradas inválidas | ruta inexistente · ruta de archivo | `InvalidInputError` con mensaje que nombra el problema | ✅ passed (2 tests, `match` sobre el mensaje) | pytest `TestEntradasInvalidas` |
| CA-7 Estabilidad Unicode y mayúsculas | `camion/camión/cama.jpg` · `Bravo.jpg` vs `alfa.jpg` | orden estable entre ejecuciones; caja ignorada en la primaria | ✅ passed (2 tests) | pytest `TestEstabilidadDeNombres` |
| CA-8 No destructivo | bytes y `st_mtime_ns` antes/después del escaneo | idénticos | ✅ passed | pytest `TestNoDestructivo` |
| CA-9 Cobertura ≥80% | `pytest --cov=media_optimizer.ingest` | ≥80% | ✅ **100%** (33/33 stmts) | log de cobertura |
| CA-10 Batería completa | pytest · ruff check/format · mypy | todo exit 0 | ✅ 92 passed · limpio · Success (10 archivos) | log de cierre |
| CA-11 Trazabilidad | gate-log HU-001 | draft/gate_spec/dev | ✅ + qa/done de este cierre | gate-log.jsonl |

**Resultado: 11/11 criterios cumplidos · 0 fallidos · sin rework.**
Capa secundaria (etiquetada): rutas absolutas utilizables, anidamiento profundo (4 niveles), resultado inmutable.

## Commits relevantes
- `e88b53a` — HU-001 DRAFT+SPEC (89%, 0 bloqueantes)
- `efbd559` — HU-001 DEV: scanner + tests (nace `ingest/`)
- `bf36345` — merge PR #9 a `develop`
