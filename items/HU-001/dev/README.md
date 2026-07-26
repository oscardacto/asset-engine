# HU-001 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/ingest/scanner.py` | `scan_input_folder(root, recursive=True) -> tuple[Path, ...]`: recorrido sin seguir symlinks de carpeta, omite ocultos y directorios, valida la raíz con `InvalidInputError`, y ordena por clave `(NFC-casefold, NFC, cruda)` |
| `src/media_optimizer/ingest/__init__.py` | Nace el paquete `ingest/` (decisión A-1, pendiente de ratificar con el merge) |
| `tests/ingest/test_scanner.py` | 15 tests: orden determinista, recursividad, qué se incluye/omite, entradas inválidas, estabilidad de nombres, no-destructividad + capa secundaria |

Primer consumidor real de dos HUs previas: `InvalidInputError` (HU-161) para las rutas
inválidas y `write_jpeg`/`flat_image` (HU-166) para poblar las carpetas de prueba con
archivos decodificables reales — cero medios del cliente.

Ajuste sobre la spec: la clave de orden quedó con **tres** componentes en vez de dos. Dos
nombres distintos pueden normalizar a la misma forma NFC (p. ej. la misma "ó" precompuesta
y descompuesta, que NTFS sí permite coexistir); sin la ruta cruda como último desempate,
el orden entre ambos habría vuelto a depender del filesystem — justo lo que la HU prohíbe.

Evidencia DEV (2026-07-26): **92 tests passed (15 nuevos) · cobertura `ingest/` 100%**
(gate ≥80%) · ruff check/format limpios · mypy estricto Success (10 archivos).
