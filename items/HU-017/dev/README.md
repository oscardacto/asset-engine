# HU-017 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/pipeline/stages.py` | `execute_stage` con medición (tiempo + memoria pico) + ejecutor de `ingest` |
| `src/media_optimizer/pipeline/registry.py` | La disponibilidad pasa a **derivarse** del ejecutor |
| `src/media_optimizer/cli/commands/run.py` | Invoca la ejecución real y traduce a consola + código |
| `tests/pipeline/test_stages.py` | 15 tests de la etapa de punta a punta |
| `tests/cli/test_main.py` | E2E real: terminal → catálogo |

**HU de composición:** conecta 8 HUs cerradas (escaneo, triaje, medidas, EXIF, hash,
catálogo, workspace, CLI) en la primera etapa ejecutable. La medición vive en
`execute_stage`, una sola vez para todas las etapas futuras; `core/` sigue puro.

**La promesa no destructiva se comprueba en cada ejecución real**, reutilizando los hashes
ya calculados: si un original cambia durante la ingesta, la etapa falla nombrándolo.

**Validación con el lote real del cliente:** 109 archivos → 102 aceptados, 7 apartados
(los videos `.mp4`, cuyo soporte es E5/P2 — se apartan con causa, no tumban el lote),
16 grupos de contenido repetido. Código de salida 4 (PARTIAL), como corresponde.

**Defecto encontrado por el test E2E (rework de HU-162):** `report.py` definía su propia
constante `"catalogo.json"` mientras el catálogo real se llama `"catalog.json"` — el
reporte nunca lo habría encontrado. Causa raíz: dos fuentes de verdad para un nombre.
Corregido importando `CATALOG_FILENAME` de `ingest`.

Evidencia DEV: **478 tests (17 nuevos) · `stages.py` 95% · total 99%** · ruff y mypy limpios.
