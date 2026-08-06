# HU-013 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/ingest/reingest.py` | `AssetChange`, `MovedAsset`, `ReingestPlan` (new / unchanged / moved / removed + `has_changes`) y `plan_reingest(previous, current)` |
| `tests/ingest/test_reingest.py` | 14 tests: sin cambios, altas y bajas, renombrados, contenido cambiado, particiones disjuntas, determinismo + capa secundaria |

**El caso que la HU existía para resolver:** el ticket dice "no duplica ni reprocesa", pero
esconde un tercer caso que ninguna de las dos palabras nombra — **el archivo renombrado o
movido**. Por contenido es el mismo asset; por ruta parece uno nuevo más uno desaparecido.
Si se tratara así, HU-019 perdería las etiquetas que el usuario hubiera anotado sobre esa
foto solo porque la cambió de carpeta. Por eso `MOVED` es una categoría propia, con test
específico.

**El complemento:** mismo nombre con otro contenido **sí** es otro asset (alta + baja), que
es la consecuencia lógica de que la identidad sea el hash y no la ruta (ADR-004 §1).

**No toca disco:** compara dos catálogos ya cargados. Por eso no aparece en el inventario de
accesos al filesystem ni necesita la capa de ADR-004.

Evidencia DEV: **274 tests passed (14 nuevos) · `reingest.py` 100% · `ingest/` 97%** · ruff
y mypy limpios.
