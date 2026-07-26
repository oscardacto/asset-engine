# HU-151 — Artefactos de DEV

El entregable de esta HU es documental y vive en el árbol del repo, no en esta carpeta:

| Artefacto | Ubicación | Estado |
|---|---|---|
| ADR-001 — Gestor de entorno y dependencias: **uv** | `docs/blueprint/adr/ADR-001-gestor-entorno.md` | **Aceptado** — PR #1 (2026-07-26) |
| Convención de ADRs (`docs/blueprint/adr/ADR-NNN-slug.md`) | fijada por el propio ADR-001 | — |

Verificaciones ejecutadas en DEV (máquina de referencia, 2026-07-26 — detalle en spec §9):
`py -0p` → solo Python 3.13.2 · `python`/`pip`/`uv`/`winget`/`scoop` fuera de PATH ·
`py -m pip` → pip 25.0.1. Los comandos del ADR se redactaron contra estos hechos (CA-2).

La instalación efectiva de uv y la creación de `pyproject.toml`/`uv.lock` quedan para
**HU-150**, con el ADR ya ratificado (spec §2.2).
