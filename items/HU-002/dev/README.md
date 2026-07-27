# HU-002 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/ingest/formats.py` | `ImageFormat` (JPEG/PNG/WEBP/HEIC/AVIF), `SUPPORTED_FORMATS` (frozenset con los 3 que el stack abre de verdad), `detect_image_format(path)` y `is_supported_image(path)`. Lee 16 bytes; tres familias de firma: prefijo simple, contenedor RIFF y contenedor ISO-BMFF |
| `src/media_optimizer/ingest/__init__.py` | Re-exporta los 4 nombres nuevos |
| `tests/ingest/test_formats.py` | 18 tests: contenido sobre extensión, soportados, reconocidos-no-soportados, desconocidos, ilegible, firma≠integridad, coherencia con el stack, no-destructividad + capa secundaria |

Verificación empírica que guió el diseño (no se asumió nada): el OpenCV lockeado reporta
`JPEG/PNG/WEBP/TIFF: build` pero **`AVIF: NO`** y ninguna mención de HEIF. De ahí la
tercera categoría —reconocido pero no soportado— que permite responder "esto es HEIC,
conviértelo" en vez de "esto no es una imagen".

Dos tests que valen más que su tamaño:
- `TestCoherenciaConElStack` recorre `SUPPORTED_FORMATS` y exige que cv2 abra cada uno: si
  un re-lock futuro cambia el build, el fallo aparece en CI y no ante un lote del usuario.
- `TestFirmaNoEsIntegridad` fija por escrito que una cabecera válida con basura detrás
  sigue siendo JPEG — el comportamiento es deliberado, no un descuido.

Correcciones en DEV (ruff, antes del commit): comprensión de lista innecesaria en un
`parametrize`.

Evidencia DEV (2026-07-26): **113 tests passed (18 nuevos, +3 del scanner ya existentes) ·
cobertura `ingest/` 100%** (gate ≥80%) · ruff check/format limpios · mypy Success (11 archivos).
