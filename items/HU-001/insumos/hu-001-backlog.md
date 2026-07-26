# HU-001 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E1 (commit `f10d05e`):

> | HU-001 | Escaneo de carpeta de entrada con orden determinista e independiente del filesystem | Depende de: HU-157 | P0 | S |

Dependencia satisfecha: HU-157 **DONE** (`MediaAsset` en `core/`). Primera HU de la épica
de ingesta — es la puerta de entrada del pipeline.

## 2. Quiénes dependen de este escaneo

Fuente: `docs/blueprint/backlog.md`, E1:

> | HU-002 | Validación de formatos de imagen soportados (magic bytes, no extensión) | HU-001 |
> | HU-006 | Hash de contenido y detección de duplicados exactos | HU-001 |
> | HU-010 | Paths unicode, nombres hostiles y colisiones de nombre | HU-001 |
> | HU-003 | Validación de formatos de video soportados (codecs esperados) | HU-001, HU-154 |

⇒ El escaneo entrega **rutas**, no assets decodificados: HU-002 decide qué es imagen
válida (magic bytes) y HU-006 calcula el hash. `MediaAsset` requiere dimensiones y hash,
que aquí todavía no se conocen — el escaneo es el paso previo.

## 3. Reglas transversales aplicables

Fuente: `.claude/rules/python.md`:

> - Determinismo: **semillas fijas, sin dependencia del orden del filesystem.**
> - Entradas hostiles se validan antes de procesar (paths, formatos, tamaños, EXIF,
>   unicode, duplicados); un archivo corrupto degrada ese asset, nunca tumba el pipeline.
> - `pathlib.Path`, nunca `os.path`

Fuente: `docs/blueprint/charter.md` §6.1 y §6.3:

> **Local y determinista** — misma entrada + mismo perfil ⇒ misma salida
> **No destructivo** — originales intactos

Fuente: `.claude/CLAUDE.md` (Pre-Flight): cobertura ≥80% en el módulo tocado; manejo de
errores explícito; validación de entradas hostiles antes de procesar.

## 4. Alcance del ticket

Recorrer una carpeta de entrada y devolver la lista de archivos candidatos en un **orden
estable** que no dependa de cómo el sistema de archivos los enumere (el orden de
`os.scandir` varía entre Windows/Linux y entre ejecuciones tras modificar la carpeta).
La validación de formato (HU-002), el hash (HU-006) y los nombres hostiles (HU-010) son
HUs propias que consumen esta lista.
