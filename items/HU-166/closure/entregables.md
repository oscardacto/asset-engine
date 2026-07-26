# Entregables — HU-166

## PRs mergeados
| PR # | Repositorio | Rama | Descripción |
|------|-------------|------|-------------|
| [#8](https://github.com/oscardacto/asset-engine/pull/8) | oscardacto/asset-engine | `feature/HU-166-fixtures-sinteticos` → `develop` | Generador de fixtures sintéticos + 20 meta-tests. El merge ratifica A-1 (paquete en `src/media_optimizer/testing/`) y A-2 (sin EXIF en esta HU) |

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| N/A — el generador no persiste estado; solo escribe en `tmp_path` durante los tests | — | — | — |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

Batería ejecutada sobre `develop` post-merge (59ada01), 2026-07-26:

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 Exposiciones controladas | `flat_image(100,100,brightness=40)` · `textured_image(256,256,120,seed=7)` | media exacta 40 · media 120 ± 2 | ✅ passed (3 tests, incluye extremos 0 y 255 exactos) | pytest `TestExposiciones` |
| CA-2 Orientaciones por dimensiones | 1080×1920 · 1920×1080 · 1000×1000 | `shape` (alto, ancho, 3) correcto | ✅ passed (parametrizado, 3 casos) | pytest `TestOrientaciones` |
| CA-3 Corruptos diferenciados | JPEG válido · truncado 50% · magic falso | válido decodifica; truncado no reconstruye el original; magic falso → None | ✅ passed (3 tests) | pytest `TestCorruptos` |
| CA-4 Determinismo byte a byte | misma semilla ×2 · semillas 1 vs 2 | bytes idénticos · bytes distintos | ✅ passed (2 tests) | pytest `TestDeterminismo` |
| CA-5 Invariantes fail-fast | brillo 300, mean_brightness 300, quality 0, keep_fraction 1.0, dims 0, size 0 | `ValueError` nombrando parámetro y valor | ✅ passed (5 tests) | pytest `TestValidaciones` |
| CA-6 Tipado y lint | `mypy src/` estricto · `ruff check` + `format --check` | exit 0 | ✅ Success (8 archivos) · All checks passed · 96 formateados | log de cierre |
| CA-7 Cobertura del módulo ≥80% | `pytest --cov=media_optimizer.testing` | ≥80% | ✅ **100%** (48/48 stmts) | log de cobertura |
| CA-8 Trazabilidad | gate-log HU-166 | draft/gate_spec/dev | ✅ + qa/done de este cierre | gate-log.jsonl |

**Resultado: 8/8 criterios cumplidos · 0 fallidos · sin rework.**
Capa secundaria (etiquetada): `write_jpeg` produce archivo decodificable en `tmp_path`, `not_an_image` respeta el tamaño pedido, recorte mínimo (5%) tampoco reconstruye.

Total de la suite tras la integración: **77 tests verdes** (20 de esta HU).

## Commits relevantes
- `46dc2f4` — HU-166 DRAFT+SPEC (90%, 0 bloqueantes)
- `a6339e7` — HU-166 DEV: generador + meta-tests
- `f4afe97` — corrección: excluir de la rama los permisos de sesión arrastrados a `settings.json`
- `59ada01` — merge PR #8 a `develop`
