# HU-157 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E7 (commit `f10d05e`):

> | HU-157 | Contrato `MediaAsset` en `core/` (foto/video, dimensiones, hash, origen) | Depende de: HU-150 | P0 | M |

Dependencia satisfecha: HU-150 **DONE**. Consumidoras directas según el backlog:
HU-158 (`QualityReport`), HU-159 (`Transform`), HU-001 (escaneo), HU-005 (orientación V/H),
HU-006 (hash/duplicados), HU-012 (persistencia del catálogo).

## 2. Qué dice la constitución sobre `core/`

Fuente: `.claude/CLAUDE.md` (Componentes/módulos):

> | `core/` | Contratos del dominio: MediaAsset, QualityReport, Transform, BusinessProfile — **sin IO** |

> - **Dominio sin IO:** `core/` no importa OpenCV, ffmpeg ni filesystem (hexagonal ligera).

Fuente: `.claude/rules/python.md`:

> - `core/` y `ranking/`: funciones puras, sin IO, sin importar OpenCV/ffmpeg.
> - contratos de dominio como dataclasses (frozen cuando aplique).
> - Composición sobre herencia; fail fast en violaciones de contrato, fail safe en datos del usuario.
> - Tipado completo (mypy estricto) y docstrings en la API pública del módulo.

Cobertura exigida (CLAUDE.md, Checklist Pre-Flight): **≥95% en dominio puro (`core/`)**.

## 3. Semántica del dominio que el contrato debe soportar

- **Orientación V/H** (backlog HU-005; Maestro §8.2 audita "orientación" por foto): la
  serie del 4-abr son "verticales luminosas" — la orientación es propiedad de primera
  clase del dominio.
- **Hash de contenido** (backlog HU-006): base de la detección de duplicados exactos.
- **Origen** (charter §6.3 no destructivo): el original jamás se toca; el asset conoce su
  ruta de origen como **valor**, sin abrir el archivo (sin IO).
- **Video**: sus metadatos extendidos (duración, fps, codec) son HU-014 — NO entran en
  este contrato base.

## 4. Alcance del ticket (los 4 conceptos, literales)

`foto/video` · `dimensiones` · `hash` · `origen` — el contrato cubre exactamente eso;
todo lo demás (score, flags, transformaciones, ambientes) vive en otros contratos
(HU-158/159/160) que **componen** con este.
