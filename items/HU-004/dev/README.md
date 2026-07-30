# HU-004 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/ingest/exif.py` | `ExifOrientation` (IntEnum 1–8 con `swaps_axes`), `ExifData` (orientación, fecha, `is_present`, `is_malformed`), `read_exif(path)` / `read_exif_from_header(bytes)` y `oriented_size(size, orientation)`. Parser propio de TIFF/IFD con límites contra EXIF hostil |
| `src/media_optimizer/testing/synthetic.py` | Añade `exif_block()` y `jpeg_with_exif()` — fixtures con EXIF real, válido o roto a propósito |
| `tests/ingest/test_exif.py` | 26 tests: ausente, orientación, malformado, fecha, medidas según orientación, EXIF hostil, no-destructividad + capa secundaria |

## Dos hallazgos que cambiaron el diseño

**1. La asunción A-2 de HU-166 era falsa.** Se había documentado que "cv2 no escribe EXIF;
hará falta una dependencia nueva con su ADR". Verificado sobre el stack real: **OpenCV 5 lee
y escribe EXIF** (`imreadWithMetadata` / `imencodeWithMetadata`, ida y vuelta byte a byte).
No hizo falta dependencia ni ADR — el generador de fixtures se amplió con stdlib. La
corrección quedó anotada en el feedback de HU-166.

**2. La orientación EXIF no es un dato pasivo.** Medido:

| Imagen 48×96 con… | `imdecode` normal | con `IMREAD_IGNORE_ORIENTATION` |
|---|---|---|
| `Orientation=1` | (48, 96) | (48, 96) |
| `Orientation=6` | **(96, 48)** | (48, 96) |
| `Orientation=8` | **(96, 48)** | (48, 96) |

OpenCV **gira la imagen al abrirla**, mientras las medidas de cabecera (HU-011) siguen
siendo las crudas. Por eso el módulo expone `oriented_size` en lugar de esconder la
diferencia: HU-005 decidirá cuál usa y lo hará explícito.

## Corrección de diseño durante DEV

La primera versión usaba `cv2.imreadWithMetadata` para extraer el EXIF — funcionaba, pero
**decodifica la imagen completa**: en una foto de 200 MP eso reserva ~600 MB solo para leer
una fecha, y contradice la filosofía de esta capa (HU-002 y HU-011 evitan decodificar a
propósito). Se sustituyó por un recorrido propio del segmento APP1 sobre los bytes de
cabecera que la capa ya lee. Coste: ~20 líneas; beneficio: cero decodificación.

## Delimitación deliberada

No se lee **GPS**, aunque el EXIF lo traiga: leer coordenadas sin una política de tratamiento
sería recolectar PII sin necesidad. Ese campo pertenece a HU-034, que sí define qué hacer
con él.

Evidencia DEV (2026-07-26): **193 tests passed (26 nuevos) · `exif.py` 96%, resto de
`ingest/` y `testing/` 100%** (gate ≥80%) · ruff check/format limpios · mypy Success
(15 archivos). Las 6 líneas sin cubrir son ramas defensivas del recorrido de IFD.
