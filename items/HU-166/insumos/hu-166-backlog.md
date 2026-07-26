# HU-166 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E7 (commit `f10d05e`):

> | HU-166 | Generador de fixtures sintéticos de imagen (exposiciones, orientaciones, corruptos) | Depende de: HU-150 | P0 | M |

Dependencias satisfechas: HU-150 **DONE** · stack de visión disponible (ADR-002 Aceptado:
opencv-python-headless 5.0 + numpy 2.5, ya lockeados).

## 2. Quiénes consumen los fixtures (dicta qué debe poder generarse)

Fuente: `docs/blueprint/backlog.md`:

> | HU-020 | Brillo medio por asset (paridad ±2% con auditoría manual) | HU-158, **HU-166** |
> | HU-021 | Histograma: % de píxeles en negro aplastado |
> | HU-022 | % de altas luces quemadas |
> | HU-005 | Detección de orientación V/H (dimensiones + EXIF Orientation) |
> | HU-002 | Validación de formatos de imagen soportados (**magic bytes**, no extensión) |
> | HU-009 | Archivos **corruptos o truncados**: cuarentena con causa, pipeline sigue |
> | HU-038 | Golden test integral de análisis **sobre fixtures sintéticos** |
> | HU-185 | Smoke test E2E **con dataset sintético** en CI local (< 60 s) |

⇒ Los tres ejes del ticket: **exposiciones** (brillo controlado: subexpuesta / media /
quemada, para HU-020–022), **orientaciones** (dimensiones V/H/cuadrada, para HU-005) y
**corruptos** (truncado, magic bytes falsos, vacío, para HU-002/009).

## 3. Reglas transversales aplicables

Fuente: `docs/blueprint/charter.md` §6.6 (PII local):

> los medios del cliente jamás salen de la máquina ni entran al repo; **fixtures de test
> sintéticos o libres**.

Fuente: `.claude/rules/python.md`:

> - Determinismo: **semillas fijas**, sin dependencia del orden del filesystem.

Fuente: `.claude/CLAUDE.md` (Pre-Flight): cobertura ≥80% en el módulo tocado (esto NO es
`core/` — es infraestructura de plataforma con numpy/cv2 permitidos).

## 4. Alcance del ticket

Generar imágenes sintéticas con propiedades **controladas y verificables** (brillo medio
objetivo, dimensiones, archivos rotos de formas específicas), de forma **determinista**
(misma semilla ⇒ mismos bytes). Los fixtures de video son HU-167 (P2, fuera). El
framework de golden tests que los consumirá es HU-164 (fuera).
