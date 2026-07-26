# HU-150 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E7 (commit `f10d05e`):

> | HU-150 | Esqueleto del repo: `pyproject.toml`, layout `src/`, ruff+mypy+pytest
> configurados con los límites de `.claude/rules/python.md` | Depende de: — | P0 | M |

Posición en el orden de arranque: segunda (`HU-151 → HU-150 → HU-152 → …`). Casi todas
las HUs de E7/E1/E2 dependen de ella directa o transitivamente.

## 2. Decisión de stack que consume (ADR-001 — Aceptado)

Fuente: `docs/blueprint/adr/ADR-001-gestor-entorno.md` (ratificado vía PR #1, 2026-07-26):

> **uv** como gestor único de entorno, dependencias y versión de Python.
> - `pyproject.toml` con `requires-python = ">=3.12"` (estándar — no acopla a uv).
> - `uv.lock` **comiteado** al repo; `.python-version` fija la versión de desarrollo.
> - La instalación efectiva de uv y la creación del proyecto ocurren en **HU-150**, ya con
>   este ADR ratificado.

Comandos de instalación (ADR §Comandos, verificados contra la máquina de referencia):

> ```powershell
> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
> # alternativa: py -m pip install --user uv
> ```

## 3. Límites que la configuración debe materializar

Fuente: `.claude/rules/python.md` (con los deltas de gobernanza del 26-jul):

> - Módulo ≤ 300 líneas · clase ≤ 200 líneas · función ≤ 40 líneas · ≤ 5 parámetros · anidamiento ≤ 3 niveles
> - Complejidad ciclomática ≤ 10 (ruff: `mccabe` C901)
> - Seguridad: prohibidos `eval`/`exec`, `pickle.loads` sobre datos no confiables, `yaml.load` sin
>   `SafeLoader` y `subprocess(..., shell=True)` […] Verificable con las reglas `S` (flake8-bandit) de
>   ruff cuando exista `pyproject.toml` (HU-163).
> - `pathlib.Path`, nunca `os.path` […] cero `print()` en código de librería.

## 4. Arquitectura de módulos objetivo y comandos convención

Fuente: `.claude/CLAUDE.md` (Componentes/módulos + Comandos de Consola):

> `core/` · `vision/` · `photo/` · `video/` · `ranking/` · `profiles/` · `pipeline/` ·
> `cli/` · `config/` · `tests/` · `benchmarks/`

> | Calidad | pytest · coverage · ruff · mypy |

> ```
> pytest · pytest --cov · ruff check . && ruff format --check . · mypy src/
> ```

Fuente: `docs/blueprint/charter.md` §6: Python del stack "3.12+"; determinismo y KPI de
reproducibilidad 100% (§7) — el lockfile del esqueleto es la primera materialización.
