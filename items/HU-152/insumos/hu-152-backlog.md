# HU-152 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E7 (commit `f10d05e`):

> | HU-152 | `ADR` OpenCV+NumPy como base de visión (versiones, wheels CPU) | Depende de: HU-150 | P0 | S |

Dependencia satisfecha: HU-150 está **DONE** (PR #2 mergeado; esqueleto con uv operativo).
Primeras consumidoras: HU-166 (fixtures sintéticos), HU-020–023 (brillo, histograma, nitidez)
y todo `vision/` / `photo/`.

## 2. Restricciones del charter que condicionan la decisión

Fuente: `docs/blueprint/charter.md` §6:

> 2. **CPU-only** — sin dependencia de GPU. Presupuestos de rendimiento por etapa en `benchmarks/`.
> 1. **Local y determinista** — […] misma entrada + mismo perfil ⇒ misma salida, byte a
>    byte donde el formato lo permita.
> 7. **Dispositivo de captura de referencia:** celular gama media […] El pipeline asume
>    medios de celular, no de cámara profesional.

## 3. Stack propuesto y reglas aplicables

Fuente: `.claude/CLAUDE.md` (Stack tecnológico):

> | Visión por computador | OpenCV + NumPy (ADR pendiente) |

Fuente: `.claude/rules/python.md`:

> - `core/` y `ranking/`: funciones puras, sin IO, sin importar OpenCV/ffmpeg.
> - […] evitar copias innecesarias de arrays NumPy — pero nunca a costa del determinismo.

Fuente: `docs/blueprint/adr/ADR-001-gestor-entorno.md` (Aceptado): las dependencias se
agregan con `uv add` y quedan fijadas en `uv.lock` (hashes, multiplataforma).

## 4. Riesgo heredado a verificar

Fuente: `items/HU-151/spec/spec_tecnica.md` §8:

> | R-1 | Wheels de OpenCV incompatibles con Python 3.13 en Windows | técnico | baja |
> medio | Se verifica en HU-152; si pasa, la herramienta debe poder fijar 3.12 por
> proyecto (uv: `uv python pin`) |

Entorno real (verificado en HU-150): CPython 3.13.2 · Windows 10 Pro 19045 · uv 0.11.32.

## 5. Operaciones de visión que el backlog exige (qué debe cubrir la librería)

Fuente: `docs/blueprint/backlog.md` E2/E3: histogramas y brillo (HU-020–022), varianza de
Laplaciano / Tenengrad (HU-023), CLAHE (HU-051), white balance (HU-052), corrección de
perspectiva/verticales (HU-028/050), crops y resize de calidad (HU-058/060) — todas
operaciones de los módulos principales de OpenCV (`core`, `imgproc`), sin `contrib`.
