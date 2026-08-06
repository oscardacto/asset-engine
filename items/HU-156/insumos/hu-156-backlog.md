# Insumo — HU-156 en el backlog

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-156 | Logging estructurado base (JSON lines, niveles, cero `print`) | HU-150 | P0 | S |

## Reglas del proyecto que la gobiernan

- `python.md`: *"Logging estructurado del proyecto — cero `print()` en código de librería."*
  Ya verificable: la regla `T20` de ruff está activa en `pyproject.toml`.
- ADR-003: los JSON del proyecto se serializan con **claves ordenadas** y `ensure_ascii=False`.
- ADR-004: *"todo acceso físico al disco pasa por la capa de adaptación del filesystem"*.
- Charter §6.1: determinismo — pero un log lleva marca de tiempo, así que **no** es una
  salida comparable. Misma tensión que resolvió HU-168.

## Evidencia medida antes de escribir la spec (2026-08-06, Windows 10 Pro 19045)

`logging.FileHandler` de la biblioteca estándar normaliza la ruta internamente con
`os.path.abspath`, que es exactamente la función que HU-010 demostró destructiva. Resultado
sobre las rutas que la capa de ADR-004 sí rescata:

| Ruta | `FileHandler` tal cual | Pasada por `system_path()` |
|------|------------------------|----------------------------|
| Larga, 383 caracteres | ❌ `FileNotFoundError` | ✅ escribe |
| `CON.log` | ❌ `ValueError: Must have exactly one of read or write mode` | ✅ 6 bytes en disco |
| `NUL.log` | ⚠️ **No protesta** — `abspath` la convierte en `\.\NUL` y **todos los registros se pierden en silencio** | ✅ 6 bytes en disco |
| `COM1.log` | ❌ `FileNotFoundError` (`\.\COM1`) | ✅ escribe |

**El caso grave es `NUL.log`, que no falla.** Un sistema de observabilidad que reporta éxito
mientras descarta cada línea es peor que uno que se cae: no hay señal de que falte nada.

Script de la medición: `items/HU-156/dev/probe_filehandler.py`.

## Consumidores

| ID | HU | Qué le pide |
|----|----|-------------|
| HU-180 | Orquestador: un asset que falla degrada, el lote continúa | Registrar cada degradación sin tumbar el run |
| HU-183 | Métricas de run en JSONL | El mismo mecanismo de escritura JSON-lines |
| HU-017, HU-037, HU-184 | Comandos de la CLI | Diagnóstico de lo que pasó en el run |
