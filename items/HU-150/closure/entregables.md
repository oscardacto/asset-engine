# Entregables — HU-150

## PRs mergeados
| PR # | Repositorio | Rama | Descripción |
|------|-------------|------|-------------|
| [#2](https://github.com/oscardacto/asset-engine/pull/2) | oscardacto/asset-engine | `feature/HU-150-esqueleto-repo` → `develop` | Esqueleto del repo: pyproject, src/, tests/, uv.lock, tooling. El merge ratifica además la asunción A-1 (paquete `media_optimizer`) |

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| Instalador standalone de uv (Astral, comando del ADR-001) | Máquina de referencia (Windows 10) | 2026-07-26 | ✅ uv 0.11.32 en `%USERPROFILE%\.local\bin` |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

Batería re-ejecutada sobre `develop` **después del merge** (51bfa10), 2026-07-26:

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 uv instalado conforme al ADR | `uv --version` | responde | ✅ `uv 0.11.32 (x86_64-pc-windows-msvc)` | log de cierre |
| CA-2 Proyecto sincronizable y lockeado | `uv sync` en develop | `.venv` sincronizado; lock con hashes; archivos comiteados | ✅ 16 paquetes resueltos en 1 ms (lock estable); `uv.lock` con 220 hashes sha256; pyproject/uv.lock/.python-version en el repo | log + `git show 51bfa10 --stat` |
| CA-3 Tests en verde | `uv run pytest` | exit 0 | ✅ 1 passed in 0.01s | log de cierre |
| CA-4 Lint/formato con límites del estándar | `uv run ruff check .` + `format --check .` | exit 0; config con C901=10, max-args=5, reglas S | ✅ "All checks passed!" · 40 archivos formateados · config verificada en `pyproject.toml` | log + pyproject `[tool.ruff.lint]` |
| CA-5 Tipado estricto limpio | `uv run mypy src/` | exit 0 en `strict` | ✅ "Success: no issues found in 1 source file" | log de cierre |
| CA-6 Layout importable y tipado | `uv run python -c "import media_optimizer; print(...)"` | imprime `0.1.0` | ✅ `0.1.0`; `py.typed` presente | log de cierre |
| CA-7 Trazabilidad del ciclo | gate-log filtrado HU-150 | `draft`, `gate_spec`, `dev` | ✅ los 3 eventos + `qa`/`done` de este cierre | `items/_metrics/gate-log.jsonl` |

**Resultado: 7/7 criterios cumplidos · 0 fallidos · sin rework.**

## Commits relevantes
- `c825273` — HU-150 DRAFT+SPEC (spec 90%, 0 bloqueantes)
- `a6ec331` — HU-150 DEV: esqueleto completo con batería en verde
- `51bfa10` — merge PR #2 a `develop`
