# HU-010 — Inventario de la superficie de impacto

> Búsqueda exhaustiva de todo acceso físico al filesystem en el repositorio, previa a la
> implementación. Base: `develop` + rama `feature/HU-010-nombres-hostiles` (2026-07-26).
>
> **Patrones buscados:** `open(`, `.open(`, `read_bytes`, `write_bytes`, `read_text`,
> `write_text`, `.stat(`, `.exists(`, `.is_file(`, `.is_dir(`, `.walk(`, `.iterdir(`,
> `.glob(`, `.rglob(`, `.mkdir(`, `.rename(`, `.unlink(`, `os.`, `shutil.`, `cv2.imread`,
> `cv2.imwrite`.

## 1. Código de producción (`src/`) — TODO debe migrar

| # | Archivo | Función | Operación | Librería | ¿Migrar? |
|---|---|---|---|---|---|
| 1 | `ingest/scanner.py:32` | `_validate_root` | exists | pathlib | **Sí** |
| 2 | `ingest/scanner.py:35` | `_validate_root` | is_dir | pathlib | **Sí** |
| 3 | `ingest/scanner.py:41` | `_walk_tree` | walk (recursivo) | pathlib | **Sí** — es la causa de I-2 (rutas largas perdidas) |
| 4 | `ingest/scanner.py:49` | `_list_top_level` | iterdir | pathlib | **Sí** |
| 5 | `ingest/scanner.py:50` | `_list_top_level` | is_file | pathlib | **Sí** |
| 6 | `ingest/formats.py:66` | `_read_header` | open + read | pathlib | **Sí** |
| 7 | `ingest/hashing.py:45` | `compute_content_hash` | open + read por bloques | pathlib | **Sí** |
| 8 | `ingest/dimensions.py:80` | `read_image_size_from_path` | open + read | pathlib | **Sí** |
| 9 | `ingest/exif.py:81` | `read_exif` | open + read | pathlib | **Sí** |
| 10 | `ingest/quarantine.py:151` | `_file_size` | stat | pathlib | **Sí** |
| 11 | `ingest/quarantine.py:174` | `_read_bytes` | open + seek + read | pathlib | **Sí** — y **se elimina**: lo sustituye el `read_bytes` de la capa |
| 12 | `testing/synthetic.py:66` | `write_jpeg` | write_bytes | pathlib | **Sí** — es `src/`, aunque sirva a tests |

**Total: 12 puntos reales en 6 archivos.** Ninguno usa `os`, `shutil`, `cv2.imread` ni
`cv2.imwrite`: la superficie es más pequeña de lo que la matriz sugería, porque toda la
ingesta se construyó sobre `pathlib`.

### Falsos positivos descartados (revisados uno a uno)
| Coincidencia | Por qué no cuenta |
|---|---|
| `core/transform.py:20` | El patrón `os\.` casó con "parámetros." en una docstring |
| `quarantine.py:72,79,81` | Texto de docstring y `list.append` |
| `quarantine.py:128,163,168` | Llaman al helper interno, no al filesystem |

### Verificación de ausencias
- **`core/`**: cero accesos a disco — confirma la regla de dominio sin IO (charter §6.4).
- **`cv2.imread` / `cv2.imwrite`**: **no se usan en ningún punto de `src/`**. La decodificación
  futura (E2) deberá nacer usando la capa; ADR-004 ya lo obliga.

## 2. Fuera de este inventario, con acción asignada

| Elemento | Situación | Acción |
|---|---|---|
| `ingest/catalog.py` (HU-012) | **No existe aún en `develop`**; su spec está aprobada en rama aparte y define `save_catalog`/`load_catalog` con escritura atómica | **Nace usando la capa** (`replace_atomic`). Anotado como dependencia en la spec de HU-010 §10 |
| Cadena de video (ffmpeg, PySceneDetect) | No instalada | HU-154, obligada a pasar la matriz antes de adoptarse |
| Salidas del directorio de trabajo | No existen aún | HU-016, que además sanea nombres al escribir |

## 3. Tests (`tests/`) — 240 coincidencias en 7 archivos, **no migran**

Se acogen a la excepción documentada en ADR-004 y en `python.md`. Dos usos distintos, ambos
legítimos:

| Uso | Ejemplo | Por qué no migra |
|---|---|---|
| **Sembrar fixtures** | `destino.write_bytes(contenido)`, `tmp_path` | Crear un caso hostil (`CON.jpg`, punto final) exige precisamente **saltarse** la normalización que la capa aplica. Si el fixture pasara por la capa, el caso a probar no podría existir |
| **Verificar el disco** | `ruta.read_bytes()`, `ruta.stat().st_mtime_ns` en los tests de no-destructividad | La aserción es sobre el estado real del archivo; mediarlo por la capa probaría la capa, no el invariante |

**Lo que sí debe cambiar en tests:** ninguna llamada al *código bajo prueba* puede
puentear la capa. El test de cumplimiento (§8.4 de la spec) vigila `src/`, no `tests/`.

## 4. Resumen para la decisión

- **Superficie total a migrar: 12 puntos, 6 archivos, 1 sola librería (`pathlib`).**
- **Uno de los 12 desaparece** en la migración (`quarantine._read_bytes`, duplicado de lo
  que ofrecerá la capa).
- **Cero uso actual de `os`, `shutil` o `cv2` sobre rutas** en producción — no hay
  sorpresas ocultas.
- **`core/` está limpio**, así que la migración no toca el dominio puro ni sus 57 tests.
- El riesgo no es de complejidad sino de **omisión**, y por eso el test de cumplimiento se
  escribe **antes** de migrar: primero debe fallar señalando los 12 puntos, y quedar en
  verde solo cuando no queda ninguno.
