# Entregables — HU-004

## Integración
| Merge | Repositorio | Rama | Descripción |
|-------|-------------|------|-------------|
| `6e47375` | oscardacto/asset-engine | `feature/HU-004-exif-seguro` → `develop` | Lectura tolerante de EXIF + fixtures con EXIF real. Integrado por Claude con batería verificada sobre la rama fusionada. Ratifica A-1 (solo orientación y fecha) y A-4 (EXIF roto degrada, no es `CorruptMediaError`) |

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| Verificación de capacidades EXIF de OpenCV 5 (ida y vuelta + rotación al decodificar) | Máquina de referencia | 2026-07-26 | ✅ ejecutada **antes** de especificar |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

Batería ejecutada sobre `develop` con el merge aplicado (`6e47375`), 2026-07-26:

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 EXIF ausente | JPEG sin metadatos | `is_present=False`, sin excepción | ✅ passed | pytest `TestExifAusente` |
| CA-2 Orientación leída | EXIF con Orientation 1, 6 y 8 | valor tipado correcto en cada caso | ✅ passed (parametrizado) | pytest `TestOrientacion` |
| CA-3 Malformado degrada | bloque truncado a la mitad · cabecera TIFF inválida | `is_malformed=True`, sin excepción | ✅ passed (2 tests) | pytest `TestExifMalformado` |
| CA-4 Valor inválido ignorado | `Orientation = 99` | `orientation is None` + malformado | ✅ passed | pytest `TestOrientacion` |
| CA-5 Fecha de captura | `DateTimeOriginal = "2026:04:04 15:30:00"` · fecha con formato inválido | datetime correcto · `None` + malformado | ✅ passed (2 tests) | pytest `TestFechaDeCaptura` |
| CA-6 Discrepancia de medidas explícita | 48×96 con Orientation 6 / 1 / 180 / None | 96×48 al girar; sin cambio en el resto | ✅ passed (2 tests) | pytest `TestMedidasSegunOrientacion` |
| CA-7 EXIF hostil | puntero de sub-IFD fuera del bloque · contador de 60.000 entradas · bloque cortado a mitad de entrada | sin excepción, sin lectura fuera de rango, marcado malformado | ✅ passed (3 tests) | pytest `TestExifHostil` |
| CA-8 No destructivo | bytes y `st_mtime_ns` antes/después | idénticos | ✅ passed | pytest `TestNoDestructivo` |
| CA-9 Cobertura ≥80% | `pytest --cov` sobre `ingest` y `testing` | ≥80% | ✅ `exif.py` **96%**, resto de módulos 100% (total 99%) | log de cierre |
| CA-10 Batería completa | pytest · ruff check/format · mypy | todo exit 0 | ✅ 193 passed · limpio · Success (15 archivos) | log de cierre |
| CA-11 Trazabilidad | gate-log HU-004 | draft/gate_spec/dev | ✅ + qa/done de este cierre | gate-log.jsonl |

**Resultado: 11/11 criterios cumplidos · 0 fallidos · sin rework.**
Capa secundaria (etiquetada): conjunto de orientaciones que intercambian ejes, orientación y fecha juntas, archivo no-JPEG, 5 formas de cabecera JPEG sin EXIF utilizable, inmutabilidad.

## Efecto colateral en un WorkItem ya cerrado
La asunción **A-2 de HU-166** ("cv2 no escribe EXIF; hará falta dependencia con ADR")
resultó **falsa** en OpenCV 5. La corrección quedó anotada en `items/HU-166/closure/feedback.md`
y el generador de fixtures se amplió **sin añadir dependencias ni abrir un ADR**.

## Commits relevantes
- `2eb7137` — HU-004 DRAFT+SPEC (89%, 0 bloqueantes) con la verificación del stack
- `b6f28b1` — HU-004 DEV: `exif.py` + fixtures EXIF + tests
- `6e47375` — merge a `develop`
