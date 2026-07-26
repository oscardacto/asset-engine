# HU-157 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/core/media_asset.py` | Contrato `MediaAsset` (frozen, slots) + enums `MediaType` y `Orientation`; invariantes fail-fast en `__post_init__`; propiedad pura `orientation` |
| `src/media_optimizer/core/__init__.py` | Nace el paquete `core/`; re-exporta la API pública |
| `tests/core/test_media_asset.py` | 17 tests organizados por CA (spec §11) + capa secundaria de boundary values etiquetada |

Pureza verificada: `core/` importa solo stdlib (`dataclasses`, `enum`, `pathlib`) — sin
OpenCV, sin numpy, sin IO. Convención sembrada (asunción A-1 ratificable en el PR):
identificadores en inglés, docstrings en español.

Evidencia DEV (2026-07-26): **17 passed · cobertura `core/` 100%** (exige ≥95%) ·
ruff check/format limpios · mypy estricto Success (3 archivos).
