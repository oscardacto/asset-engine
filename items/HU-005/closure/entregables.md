# Entregables — HU-005

## Integración
| Merge | Rama | Descripción |
|-------|------|-------------|
| `7b9625e` | `feature/HU-005-orientacion` → `develop` | Orientación efectiva vs cruda. Batería verificada sobre la rama fusionada. Ratifica A-1 (manda la efectiva) y A-3 (no se persiste todavía) |

## Evidencia contra los criterios de aceptación (spec §11)

| CA | Resultado | Evidencia |
|----|-----------|-----------|
| CA-1 Sin EXIF: efectiva = cruda | ✅ | `TestSinMetadato` (4 tests, incluye los 3 casos V/H/cuadrada) |
| CA-2 Valores 1-4 no giran | ✅ | parametrizado sobre los cuatro |
| CA-3 Valores 5-8 giran | ✅ | parametrizado, en ambos sentidos (H→V y V→H) |
| CA-4 Cuadrada girada sigue cuadrada | ✅ | parametrizado sobre los cuatro que giran; `rotated` falso |
| CA-5 Función pura | ✅ | `TestDeterminismo` |
| CA-6 `core.Orientation` intacto | ✅ | los tests de HU-157 pasan sin modificación |
| CA-7 Test de arquitectura verde | ✅ | `core` sigue sin importar `ingest` |
| CA-8 Cobertura y batería | ✅ | `ingest/` **97%**, 260 passed + 1 skipped, ruff y mypy limpios |
| CA-9 Trazabilidad | ✅ | gate-log completo |

**Resultado: 9/9 · 0 fallidos · sin rework · verde en la primera ejecución.**

## Commits relevantes
- `bcb9427` — DEV: `orientation.py` + 24 tests (incluye DRAFT+SPEC, gate 91%)
- `7b9625e` — merge a `develop`
