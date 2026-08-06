# HU-156 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/logs.py` | `JsonLinesFormatter`, `FilesystemFileHandler`, `configure_logging`, `get_logger` |
| `tests/test_logs.py` | 20 tests: formato, campos del llamador, niveles, idempotencia, **rutas que la stdlib pierde** |
| `tests/test_arquitectura.py` | La regla de ADR-004 pasa a detectar handlers que abren el archivo por dentro |
| `dev/probe_filehandler.py` | El script con el que se midió el defecto, ejecutable |

**La biblioteca estándar no servía, y se midió antes de escribir la spec.**
`logging.FileHandler` normaliza la ruta con `os.path.abspath` — la misma función que HU-010
demostró destructiva. Resultado sobre las rutas que la capa sí rescata:

| Ruta | `FileHandler` tal cual | Pasada por la capa |
|---|---|---|
| Larga (383 car.) | ❌ `FileNotFoundError` | ✅ |
| `CON.log` | ❌ `ValueError` | ✅ |
| `NUL.log` | ⚠️ **no protesta y descarta todo** | ✅ |
| `COM1.log` | ❌ `FileNotFoundError` | ✅ |

**El caso grave es el que no falla.** Un sistema de diagnóstico que reporta éxito mientras
tira cada línea no deja señal de que falte algo. Por eso las pruebas comprueban **bytes en
disco**, no ausencia de excepción: una prueba de "¿lanzó error?" habría dado verde con el
handler roto.

**Se verificó que las pruebas no pasan en vacío.** Sustituido el handler propio por el de la
stdlib, caen 4 de las 5 pruebas de rutas hostiles.

**Segundo hallazgo, de gobernanza.** El test de arquitectura vigilaba `open`, `os.*` y los
métodos de `Path`, pero **no veía** `logging.FileHandler(ruta)`: una clase de terceros que
abre el archivo por dentro. El hueco queda cerrado, y también se comprobó por inyección —
con el handler estándar en producción, la regla ahora sí lo denuncia. Heredar de la clase
para adaptarla sigue permitido, que es justo lo que hace la capa.

Evidencia DEV: **401 tests passed (25 nuevos) · `logs.py` 100%** · ruff y mypy limpios.
