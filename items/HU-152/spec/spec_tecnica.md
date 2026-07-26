# Spec Técnica `HU-152` — `ADR OpenCV+NumPy como base de visión (versiones, wheels CPU)`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 91% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** cerrar con un ADR la fila "OpenCV + NumPy (ADR pendiente)" del stack:
  qué variante de wheel, qué estrategia de versiones, y **verificación empírica** de que
  los wheels CPU funcionan en la máquina de referencia (Python 3.13.2 / Windows 10).
- **Para quién:** `vision/`, `photo/` y las HUs de E2/E3; desbloquea HU-166 y HU-020+.
- **Módulo / dominio:** plataforma (E7) — ADR-002 + dependencias de runtime en pyproject.
- **No obvio (lo crítico que el ticket no dice de frente):** la elección real no es
  "OpenCV sí/no" (eso ya lo propone el stack) sino **qué variante**: el wheel `full`
  arrastra GUI (Qt/highgui) que una CLI jamás usa — la variante `headless` es la que
  encaja con "local, CLI, sin GUI en v1". Y "verificar wheels" significa ejecutar, no
  leer changelogs: importar, comprobar build CPU y correr una operación determinista.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- Redacción de `ADR-002` (variante de wheel, estrategia de versiones, consecuencias para
  determinismo y mypy) — estado **Propuesto**, se ratifica con el merge.
- `uv add` de las dependencias decididas → `pyproject.toml` + `uv.lock` actualizados.
- Verificación empírica en la máquina de referencia: import, versiones, build info sin
  CUDA, operación determinista repetible.
- Test permanente de humo del stack de visión (`tests/test_stack_vision.py`) para que
  cualquier futuro update del lock re-verifique los wheels automáticamente.

### 2.2 OUT — NO entra (delimitaciones)
- Crear el módulo `vision/` o cualquier primitiva de visión → HU-023+, nacen con sus HUs.
- Política de threads/determinismo de OpenCV en código de producción → se documenta como
  consecuencia en el ADR; se materializa cuando exista `vision/`.
- ADRs de video (HU-154) y catálogo (HU-153).
- Benchmarks de rendimiento de operaciones (HU-165 y presupuestos por etapa).

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | "wheels CPU" | El build instalado no debe requerir GPU (charter §6.2: CPU-only) | backlog HU-152 · charter §6 |
| 2 | R-1 heredado: wheels vs Python 3.13/Windows | Verificación empírica; si fallara, `uv python pin 3.12` (mitigación ya prevista en ADR-001) | HU-151 spec §8 |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- ¿Módulos `contrib` necesarios a futuro? → P-1.
- Debugging visual sin `cv2.imshow` (headless) → P-2.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `docs/blueprint/adr/ADR-002-stack-vision.md` | nuevo | bajo | ✅ no existe; convención de ADRs vigente (ADR-001) |
| `pyproject.toml` `[project].dependencies` | modif (hoy `[]`, verificado) | bajo | ✅ develop `1162ac3` |
| `uv.lock` | regenerado por `uv add` | bajo | ✅ lock estable (re-resolución 1 ms en cierre HU-150) |
| `tests/test_stack_vision.py` | nuevo | bajo | ✅ no existe |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| Esqueleto HU-150 (uv, pytest, ruff con `per-file-ignores` para tests) | Sí | El test de humo entra al harness existente sin tocar config |
| Convención y formato de ADR-001 | Sí | ADR-002 replica estructura y ciclo Propuesto→Aceptado |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| N/A | — | — | N/A |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "CPU-only — sin dependencia de GPU" | charter §6.2 | No | Wheels PyPI estándar (build CPU); el test de humo verifica ausencia de CUDA en build info |
| RN-2 | "Local y determinista … misma salida" | charter §6.1 | No | La operación de visión de referencia debe producir bytes idénticos en ejecuciones repetidas |
| RN-3 | "`core/` y `ranking/` … sin importar OpenCV" | `python.md` | No | La dependencia entra al proyecto pero su superficie de import queda confinada a `vision/`/`photo/`/`video/` (se vigila en revisión; regla ya inyectada por hook en cada edición .py) |
| RN-4 | GUI fuera de alcance v1 | charter §5 | No | Variante `headless` es coherente; `cv2.imshow` no disponible es aceptable |
| RN-5 | Dependencias con ADR + lock (ADR-001) | CLAUDE.md · ADR-001 | No | `uv add` en la rama del ADR; el merge ratifica ADR y dependencia a la vez (patrón HU-151) |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | `import cv2` + `import numpy` funcionan en 3.13.2/Windows tras `uv sync` | Se activa mitigación R-1: `uv python pin 3.12` + re-lock (y el ADR lo documenta) |
| V-2 | Batería del esqueleto sigue verde tras `uv add` (pytest+ruff+mypy) | La HU no pasa a QA |

---

## 6. Preguntas abiertas

### P-1 — ¿Se necesitarán módulos `contrib` (opencv-contrib) en alguna HU del backlog?
- **Categoría:** INFORMATIVA
- **Importa porque:** cambiar de wheel después implica desinstalar/reinstalar variante (excluyentes entre sí).
- **Va dirigida a:** equipo técnico (se re-evalúa por HU).
- **Mi mejor hipótesis:** no — el inventario de operaciones del backlog (insumo §5) se cubre con `core`+`imgproc` estándar; YAGNI manda.
- **Si se asume mal, costo:** swap de dependencia + actualización del ADR (~1 h), sin cambios de API.
- **Estado:** ABIERTA

### P-2 — ¿Alguien del equipo depende de `cv2.imshow` para debugging visual?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** no — el flujo del producto es CLI y "no destructivo con directorio de trabajo": el debugging visual natural es exportar imágenes a archivo y abrirlas con el visor del SO.
- **Si se asume mal, costo:** `uv add` temporal de la variante full en un entorno local de quien lo necesite; el proyecto no cambia.
- **Estado:** ABIERTA

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Variante `opencv-python-headless` (sin GUI) es suficiente para todo v1 | P-1, P-2 | Swap de variante + ADR actualizado |
| A-2 | Floors `opencv-python-headless>=4.10` y `numpy>=2.0`; las versiones exactas las fija `uv.lock` (patrón validado en HU-150) | — | Ajustar floor y re-lock |
| A-3 | Los stubs `.pyi` que empaqueta opencv-python(-headless) desde 4.8 bastan para mypy estricto en tests/futuro `vision/` | — | `ignore_missing_imports` puntual para `cv2` (última opción) o stubs de terceros con ADR |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | Wheel cp313/win_amd64 inexistente o roto (heredado HU-151) | técnico | baja | medio | Verificación empírica en DEV; fallback `uv python pin 3.12` + re-lock |
| R-2 | Descarga pesada (~40-60 MB) falla por red | técnico | baja | bajo | Reintentar; uv cachea lo descargado |
| R-3 | Operación de OpenCV no determinista por threading interno | técnico/datos | baja | medio | Test de humo repite la operación y compara bytes; si fallara, `cv2.setNumThreads(1)` entra al ADR como requisito de `vision/` |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (2 INFORMATIVAS)
- **Asunciones tomadas:** 3
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop 1162ac3`: dependencies `[]`, esqueleto verde, lock 220 hashes)
  - [x] Entorno real cruzado: CPython 3.13.2 · uv 0.11.32 operativo · PyPI accesible (sync de HU-150 lo demostró)
  - [x] Inventario de operaciones del backlog cruzado contra módulos estándar de OpenCV (insumo §5 — sin `contrib`)
  - [x] Componentes reutilizables buscados (§3.1)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 91% — el 9%: R-1 (se resuelve empíricamente en los primeros minutos de DEV) y P-1 (YAGNI con costo de reversa bajo).

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-150 | Consume el esqueleto (uv, pyproject, tests) | DONE |
| ADR-001 | Patrón de gestión de dependencias | Aceptado |
| HU-166, HU-020–023, HU-028, HU-050–052 | Consumen esta decisión | backlog |

### 10.2 Datos/configuración previa requerida
- Red a PyPI durante `uv add` (fase de setup).

### 10.3 Servicios o equipos externos
- PyPI (wheels) — solo durante instalación/lock.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — El ADR existe y decide
- **Given:** la fila del stack "OpenCV + NumPy (ADR pendiente)"
- **When:** HU-152 completa DEV
- **Then:** existe `docs/blueprint/adr/ADR-002-stack-vision.md` con ≥2 variantes comparadas, decisión única, estrategia de versiones y consecuencias; estado `Propuesto` → `Aceptado` al merge

### CA-2 — Dependencias lockeadas sin romper el proyecto
- **Given:** `develop` con `dependencies = []`
- **When:** `uv add` de las dependencias decididas
- **Then:** `pyproject.toml` las declara con floors, `uv.lock` las fija con hashes, y `uv sync` termina OK

### CA-3 — Wheels importables en la máquina de referencia (cierra R-1 de HU-151)
- **When:** `uv run python -c "import cv2, numpy; print(cv2.__version__, numpy.__version__)"`
- **Then:** imprime ambas versiones sin error en CPython 3.13.2/Windows

### CA-4 — Build CPU-only
- **When:** se inspecciona `cv2.getBuildInformation()`
- **Then:** sin soporte CUDA activo (charter §6.2)

### CA-5 — Operación de visión determinista
- **Given:** imagen sintética con semilla fija
- **When:** la misma operación (GaussianBlur 5×5) se ejecuta dos veces
- **Then:** los arrays resultantes son idénticos byte a byte

### CA-6 — La batería del esqueleto sigue verde
- **When:** `uv run pytest` · `uv run ruff check .` + `format --check` · `uv run mypy src/`
- **Then:** todo exit 0 (ahora con 3 tests: smoke + 2 de stack de visión)

### CA-7 — Trazabilidad del ciclo
- **Then:** gate-log con `draft`, `gate_spec` y `dev` de HU-152

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial y evaluación de gate | Claude (ejecutor) |
| 2026-07-26 | DEV: ADR-002 redactado (headless, Propuesto); `uv add` resolvió **OpenCV 5.0.0.93** + NumPy 2.5.1 (dato nuevo: mayor 5.x, cubierto por el floor `>=4.10` y congelado por el lock — sin desviación de §2); R-1 cerrado empíricamente; batería 3 tests en verde | Claude (ejecutor) |
