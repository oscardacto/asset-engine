# HU-012 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/ingest/catalog.py` | `Catalog` (versión, raíz, entradas, apartados), `CatalogEntry`, `QuarantineRecord`, `save_catalog` con escritura atómica, `load_catalog` con validación campo a campo, y `catalog_from_triage` |
| `tests/ingest/test_catalog.py` | 19 tests: ida y vuelta, atomicidad, determinismo, rutas relativas, catálogo corrupto + capa secundaria |

**Nace usando la capa de ADR-004**: `save_catalog` escribe con `filesystem.write_bytes` y
sustituye con `filesystem.replace_atomic`. Ni una llamada directa al disco — el test de
gobernanza lo verifica.

**Ajuste de diseño durante DEV:** la primera versión ordenaba las entradas al *serializar*,
así que la ida y vuelta no era fiel (el objeto en memoria conservaba el orden de llegada).
Se movió el orden al **constructor del contrato**, que es lo que ADR-003 pide literalmente:
"el orden es un dato, no un accidente de ejecución". Ahora dos catálogos con el mismo
contenido son iguales y producen bytes idénticos, sin importar cómo se armaron.

**El test que más vale:** `test_el_catalogo_anterior_sobrevive_a_un_fallo` simula un corte
justo antes de sustituir y verifica que el catálogo previo queda intacto y cargable. Es la
demostración de que la escritura atómica no es una promesa del docstring.

Evidencia DEV: **236 tests passed (19 nuevos) · `ingest/` 97%** · ruff y mypy limpios.
