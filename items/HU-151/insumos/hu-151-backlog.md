# HU-151 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Las fuentes canónicas viven en el repo; ante discrepancia
> mandan las fuentes, no este extracto.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E7, tabla HU-150–169 (commit `f10d05e`):

> | HU-151 | `ADR` Gestor de entorno y dependencias (venv+pip vs uv) | Depende de: — | P0 | S |

Reglas del backlog que le aplican:

> Las HUs marcadas `ADR` cierran una decisión de stack antes de que otra HU dependa de ella.

Dependientes directas en el orden de arranque: `HU-151 → HU-150 → HU-152 → …` — HU-150
(esqueleto del repo: `pyproject.toml`, layout `src/`, ruff+mypy+pytest) es la primera
consumidora de esta decisión.

## 2. Restricciones del charter que condicionan la decisión

Fuente: `docs/blueprint/charter.md` §6 (Restricciones y principios):

> 1. **Local y determinista** — sin nube, sin APIs remotas; misma entrada + mismo perfil
>    ⇒ misma salida, byte a byte donde el formato lo permita.
> 2. **CPU-only** — sin dependencia de GPU.

Fuente: `docs/blueprint/charter.md` §7 (KPIs):

> | Reproducibilidad | 100% — misma entrada+perfil ⇒ misma salida (verificado en CI con golden tests) |

## 3. Stack propuesto en Fase 0

Fuente: `.claude/CLAUDE.md` (Stack tecnológico + Comandos de Consola):

> | Núcleo / dominio | Python 3.12+ · typing estricto · dataclasses |
> | Calidad | pytest · coverage · ruff · mypy |

> ```
> python -m venv .venv && .venv\Scripts\activate    # entorno (o uv, ADR pendiente)
> pip install -e ".[dev]"
> ```

Fuente: `.claude/CLAUDE.md` (Modo de Operación del Workspace):

> No instalar dependencias nuevas sin aprobación — y si son de stack, con su ADR.
