# Entregables — HU-012

## Integración
| Merge | Rama | Descripción |
|-------|------|-------------|
| `c8e12d7` | `feature/HU-012-catalogo` → `develop` | Catálogo con escritura atómica. Batería verificada sobre la rama fusionada. Ratifica A-1 (rutas relativas) y A-2 (versión desconocida se rechaza) |

## Evidencia contra los criterios de aceptación (spec §11)

| CA | Resultado | Evidencia |
|----|-----------|-----------|
| CA-1 Ida y vuelta fiel | ✅ | `TestIdaYVuelta` (3 tests, incluye lote vacío) |
| CA-2 El catálogo previo sobrevive a un fallo | ✅ | `test_el_catalogo_anterior_sobrevive_a_un_fallo` — simula el corte justo antes de sustituir; el archivo previo queda intacto y cargable, sin temporales sueltos |
| CA-3 Determinismo byte a byte | ✅ | mismo contenido en orden inverso ⇒ bytes idénticos |
| CA-4 Rutas relativas | ✅ | el archivo no contiene `C:` ni la ruta de la máquina; el catálogo sigue legible tras mover la carpeta |
| CA-5 Corrupto con mensaje accionable | ✅ | 5 tests: JSON inválido, no-objeto, campo ausente, tipo incorrecto, `entries` que no es lista |
| CA-6 Versión desconocida se rechaza | ✅ | el mensaje nombra la encontrada y la soportada |
| CA-7 Lote vacío válido | ✅ | `test_un_lote_vacio_es_valido` |
| CA-8 No destructivo | ✅ | escribe solo en el directorio indicado |
| CA-9 Cobertura ≥80% | ✅ | `ingest/` **97%** |
| CA-10 Batería completa | ✅ | 236 passed + 1 skipped, ruff y mypy limpios |
| CA-11 Trazabilidad | ✅ | gate-log completo |

**Resultado: 11/11 · 0 fallidos · sin rework.**

## Commits relevantes
- `0856d48` — DRAFT+SPEC (88%, 0 bloqueantes)
- `95d6933` — merge de develop (incorpora la capa de ADR-004)
- `8ae2011` — DEV: `catalog.py` + tests
- `c8e12d7` — merge a `develop`
