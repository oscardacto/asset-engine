# HU-150 — Artefactos de DEV

Los artefactos viven en la raíz del repo (son el esqueleto mismo):

| Artefacto | Qué es |
|---|---|
| `pyproject.toml` | Metadatos PEP 621 + config de ruff (C901≤10, max-args=5, reglas S/PTH/T20), mypy estricto, pytest y coverage |
| `uv.lock` | Lockfile multiplataforma — 220 hashes sha256, resuelto el 2026-07-26 |
| `.python-version` | `3.13` — versión de desarrollo fijada (CPython 3.13.2 de la máquina) |
| `src/media_optimizer/` | Paquete raíz: `__init__.py` (`__version__ = "0.1.0"`) + `py.typed` |
| `tests/test_smoke.py` | Smoke test: importa el paquete y verifica la versión |

Instalación realizada en DEV (autorizada por ADR-001 Aceptado): **uv 0.11.32** vía
instalador standalone de Astral en `C:\Users\usuario\.local\bin` (fuera del PATH hasta
reiniciar shell — mitigación R-2 de la spec: prepend por sesión).

Versiones dev lockeadas: pytest 9.1.1 · pytest-cov 7.1.0 · ruff 0.16.0 · mypy 2.3.0.

Evidencia de la batería (2026-07-26, detalle en cierre): `uv sync` OK (16 paquetes) ·
`uv run pytest` 1 passed · `uv run ruff check .` limpio · `uv run ruff format --check .`
OK · `uv run mypy src/` Success · import imprime `0.1.0`.
