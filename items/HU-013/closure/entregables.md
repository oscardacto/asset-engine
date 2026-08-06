# Entregables — HU-013

## Integración
| Merge | Rama | Descripción |
|-------|------|-------------|
| `7cdda3b` | `feature/HU-013-reingesta` → `develop` | Re-ingesta idempotente. Batería verificada sobre la rama fusionada. Ratifica A-1 (identidad por hash) y A-2 (el plan no se persiste) |

## Evidencia contra los criterios de aceptación (spec §11)

| CA | Resultado | Evidencia |
|----|-----------|-----------|
| CA-1 Catálogo consigo mismo: sin cambios | ✅ | `TestSinCambios` |
| CA-2 Archivo nuevo → `NEW` | ✅ | `TestAltasYBajas` |
| CA-3 Archivo ausente → `REMOVED` | ✅ | `TestAltasYBajas` |
| CA-4 Renombrado/movido → `MOVED`, nunca alta+baja | ✅ | `TestRenombradosYMovidos` (2 tests: renombrar y cambiar de carpeta) |
| CA-5 Mismo nombre, otro contenido → alta + baja | ✅ | `TestContenidoCambiado` |
| CA-6 Colecciones disjuntas y completas | ✅ | `TestParticiones` con lote mixto de 3+3 |
| CA-7 Determinismo | ✅ | 2 tests: mismo par, y orden de entradas alterado |
| CA-8 Primera ingesta: todo nuevo | ✅ | `test_la_primera_ingesta_es_todo_nuevo` |
| CA-9 Cobertura y batería | ✅ | `reingest.py` **100%**, `ingest/` 97%, 274 passed + 1 skipped |
| CA-10 Trazabilidad | ✅ | gate-log completo |

**Resultado: 10/10 · 0 fallidos · sin rework.**

## Commits relevantes
- `78dae9a` — DEV: `reingest.py` + 14 tests (incluye DRAFT+SPEC, gate 90%)
- `7cdda3b` — merge a `develop`
