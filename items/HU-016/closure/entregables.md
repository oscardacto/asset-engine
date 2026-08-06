# Entregables — HU-016

## Integración
| Merge | Rama | Descripción |
|-------|------|-------------|
| `e6eb522` | `feature/HU-016-directorio-trabajo` → `develop` | Directorio de trabajo + saneamiento de nombres + verificación de no-destructividad. Ratifica A-1 (módulo de nivel superior) y A-2 (sufijo numérico) |

## Evidencia contra los criterios de aceptación

| CA | Resultado | Evidencia |
|----|-----------|-----------|
| CA-1 `ensure()` crea e es idempotente | ✅ | `TestLayout` (2 tests) |
| CA-2 Nombre problemático → escribible y releíble | ✅ | parametrizado sobre 6 casos: punto y espacio final, `< > " \| ? \x00` — cada uno se escribe y se relee por ruta normal |
| CA-3 Nombre de dispositivo saneado | ✅ | parametrizado sobre `CON.jpg`, `NUL.jpg`, `COM1.jpg`, `PRN`, `con.JPG` |
| CA-4 `Foto.jpg` vs `foto.jpg` no se pisan | ✅ | `TestColisiones` + numeración de colisiones sucesivas |
| CA-5 Saneamiento determinista | ✅ | `TestDeterminismo` (2 tests) |
| CA-6 Orígenes intactos | ✅ | 3 tests: sin cambios tras escribir, detección cuando sí cambia, y que usa contenido y no `mtime` |
| CA-7 Nombre vacío → marcador | ✅ | `test_un_nombre_que_queda_vacio_recibe_un_marcador` |
| CA-8 Gobernanza verde | ✅ | `workspace` usa la capa; el test de arquitectura pasa |
| CA-9 Cobertura y batería | ✅ | `workspace.py` **100%**, 302 passed + 1 skipped |
| CA-10 Trazabilidad | ✅ | gate-log completo |

**Resultado: 10/10 · 0 fallidos · sin rework.**

## Commits
- `9b4d0d5` — DEV: `workspace.py` + `make_directory` en la capa + 20 tests
- `e6eb522` — merge a `develop`
