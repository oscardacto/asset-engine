# HU-152 — Artefactos de DEV

| Artefacto | Ubicación | Estado |
|---|---|---|
| ADR-002 — Base de visión: **opencv-python-headless + NumPy** | `docs/blueprint/adr/ADR-002-stack-vision.md` | Propuesto — se ratifica como *Aceptado* con el merge de esta rama |
| Dependencias de runtime | `pyproject.toml` (`opencv-python-headless>=4.10`, `numpy>=2.0`) + `uv.lock` (exactas: **cv2 5.0.0.93**, **numpy 2.5.1**, con hashes) | comiteadas |
| Humo permanente del stack | `tests/test_stack_vision.py` — build CPU-only + operación determinista | en verde |

Verificación empírica (2026-07-26, máquina de referencia 3.13.2/Win10) — cierra R-1 de HU-151:
`uv add` OK · import `cv2 5.0.0` / `numpy 2.5.1` · build sin CUDA · GaussianBlur ×2 →
arrays idénticos. Batería completa post-add: **3 passed** · ruff check/format limpios ·
mypy estricto sin issues.
