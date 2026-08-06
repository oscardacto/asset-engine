# HU-005 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/ingest/orientation.py` | `AssetOrientation` (raw + effective + `rotated`) y `detect_orientation(size, exif_orientation)` |
| `tests/ingest/test_orientation.py` | 24 tests: sin metadato, los 4 valores que no giran, los 4 que sí, cuadradas, determinismo + capa secundaria |

**Esta HU compone, no construye.** Las cuatro piezas que necesitaba ya existían:
`core.Orientation` (HU-157), `oriented_size` y `ExifOrientation.swaps_axes` (HU-004), e
`ImageSize` (HU-011). El módulo entero son 47 líneas. Es la señal de que las HUs previas
dejaron la superficie correcta.

**La decisión que la HU existía para tomar:** HU-004 dejó escrito que "HU-005 decidirá cuál
usa y por qué". La respuesta es **la efectiva** —la que se ve al abrir la imagen—, porque es
la que el cliente anotó en su auditoría y la que determina si una foto sirve para una story.
La cruda se conserva al lado, y `rotated` permite detectar la diferencia sin tener que
compararlas a mano.

Evidencia DEV: **260 tests passed (24 nuevos) · `ingest/` 97%** · ruff y mypy limpios, en la
primera ejecución.
