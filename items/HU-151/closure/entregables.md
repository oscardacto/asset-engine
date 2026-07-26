# Entregables — HU-151

## PRs mergeados
| PR # | Repositorio | Rama | Descripción |
|------|-------------|------|-------------|
| [#1](https://github.com/oscardacto/asset-engine/pull/1) | oscardacto/asset-engine | `feature/HU-151-adr-entorno` → `develop` | ADR-001 gestor de entorno (uv) + ciclo completo de HU-151. El merge ratifica el ADR (acto humano de aprobación) |

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| N/A — HU documental, sin código ni migraciones | — | — | — |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 El ADR existe y decide | Inspección de `docs/blueprint/adr/ADR-001-gestor-entorno.md` en `develop` | Contexto, ≥2 opciones vs charter, decisión única, consecuencias, estado en encabezado | ✅ 3 opciones (venv+pip / +pip-tools / uv), decisión uv, consecuencias con mitigación, estado ratificado | El propio archivo (commit `8cc7c7f`, mergeado en `b56985b`) |
| CA-2 Comandos reales, no aspiracionales | Re-verificación en máquina de referencia al cierre (2026-07-26) | Ningún comando del ADR depende de `python`/`pip` en PATH ni de winget | ✅ `py -0p` → solo 3.13.2 · `py -m pip` → pip 25.0.1 · `python`/`pip`/`uv`/`winget`/`scoop` confirmados NO en PATH · instalación vía `irm astral.sh` (PowerShell) o `py -m pip install --user uv` | Salida de consola registrada en esta sesión de cierre |
| CA-3 La decisión sirve el KPI de reproducibilidad | ADR §Decisión y §Consecuencias | Lockfile versionable con hashes, todas las transitivas, multiplataforma | ✅ `uv.lock` cumple los tres atributos; `pyproject.toml` PEP 621 como vía de escape sin lock-in | ADR §Decisión. Verificación operativa (primer `uv.lock` real) queda en HU-150 |
| CA-4 Trazabilidad del ciclo | `items/_metrics/gate-log.jsonl` filtrado por HU-151 | Eventos `draft`, `gate_spec` (con confianza y conteos), `dev` | ✅ `draft` · `gate_spec` intento 1, confianza 92, 0 bloqueantes · `dev` — más `qa` y `done` de este cierre | Líneas JSONL en el gate-log |

**Resultado: 4/4 criterios cumplidos · 0 fallidos · sin rework.**
Nota de alcance (spec §2.2): uv NO se instala en esta HU — la ejecutabilidad del día a día
(`uv sync`, `uv run pytest`) se evidencia en HU-150, primera consumidora del ADR.

## Commits relevantes
- `f4b9194` — HU-151 DRAFT+SPEC (insumos, spec 92%, whitelist de items/ en .gitignore)
- `8cc7c7f` — HU-151 DEV: ADR-001 (Propuesto) + convención de ADRs
- `0a78f51` · `b9918c1` — gobernanza paralela: deltas a `.claude/rules/python.md` (en `main`, sin HU)
- `b56985b` — merge PR #1 a `develop` (ratificación del ADR)
