# HU-166 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/testing/synthetic.py` | Generador determinista: `flat_image` (brillo medio exacto), `textured_image` (semilla + brillo objetivo ±2 en rango medio), `encode_jpeg`/`write_jpeg`, `truncated_jpeg` (corte a mitad de stream), `not_an_image` (magic bytes falsos) |
| `src/media_optimizer/testing/__init__.py` | Nace el paquete `media_optimizer.testing` (patrón `numpy.testing`) — importable desde tests y benchmarks |
| `tests/testing/test_synthetic.py` | 20 meta-tests: exposiciones, orientaciones, corruptos diferenciados, determinismo byte a byte, validaciones + capa secundaria |

Decisiones aplicadas de la spec: paquete en `src/` (A-1), sin EXIF (A-2 — la pregunta
queda transferida a HU-004/005), JPEG único formato (A-3), tolerancia ±2 declarada solo
en rango medio [30, 225] (A-4 — los extremos exactos los da `flat_image`).

Correcciones en DEV (atrapadas por la batería local antes del commit): signo `×` ambiguo
en docstring, 3 números mágicos promovidos a constantes (`_MAX_LEVEL`, `_MIN/_MAX_QUALITY`
— nuestra propia regla aplicada por ruff), 1 línea >100 col, y 1 rama de validación sin
cubrir (test añadido → 100%).

Evidencia DEV (2026-07-26): **77 tests passed (20 nuevos) · cobertura `testing/` 100%**
(gate ≥80%) · ruff check/format limpios · mypy estricto Success (8 archivos).
