# ADR-002 — Base de visión por computador: opencv-python-headless + NumPy

- **Estado:** Propuesto — se ratifica como *Aceptado* con el merge de `feature/HU-152-adr-opencv`
- **Fecha:** 2026-07-26
- **Origen:** HU-152 (backlog E7) · spec en `items/HU-152/spec/spec_tecnica.md`
- **Decisores:** equipo técnico (@oscardacto) · análisis: Claude (orquestador-ejecutor ASDD)

---

## Contexto

El stack propuso "OpenCV + NumPy (ADR pendiente)". Restricciones del charter §6:
**CPU-only** (sin GPU), **local y determinista**, GUI fuera de alcance v1 (§5, interfaz
CLI). Las operaciones que exige el backlog (histogramas, brillo, Laplaciano/Tenengrad,
CLAHE, white balance, warp de perspectiva, crops/resize) viven todas en los módulos
estándar `core`/`imgproc` — ninguna requiere `contrib`.

Riesgo heredado de HU-151 (R-1): disponibilidad de wheels para CPython 3.13 en Windows.
**Verificado empíricamente el 2026-07-26** en la máquina de referencia (3.13.2/Win10):

| Verificación | Resultado |
|---|---|
| `uv add` + import | ✅ `cv2 5.0.0` · `numpy 2.5.1` (wheels cp313/win_amd64) |
| Build CPU-only | ✅ `getBuildInformation()` sin CUDA activo |
| Determinismo (GaussianBlur 5×5 ×2 sobre imagen con semilla fija) | ✅ arrays idénticos byte a byte |

## Opciones consideradas

### A — `opencv-python` (wheel full, con highgui/GUI)
- ✅ Permite `cv2.imshow` para debugging visual interactivo.
- ⚠️ Arrastra dependencias de GUI (Qt) que una CLI jamás ejecuta: +peso, +superficie de
  fallos en headless/CI. El producto es CLI (charter §5) y el debugging natural del
  pipeline no destructivo es exportar a archivo y abrir con el visor del SO.

### B — `opencv-python-headless` (wheel sin GUI)
- ✅ Mismo `core`/`imgproc` que el full, sin lastre de GUI; el wheel estándar de
  servidores y pipelines. Empaqueta stubs `.pyi` (mypy estricto OK). Build CPU de PyPI —
  alineado con charter §6.2 sin configuración extra.
- ⚠️ `cv2.imshow` no disponible — aceptado (ver Contexto/opción A).

### C — `opencv-contrib-python(-headless)` (con módulos contrib)
- ✅ Acceso a `ximgproc` y extras.
- ⚠️ Nada del backlog los usa (inventario en insumo §5 de la HU) — YAGNI. Las variantes
  son mutuamente excluyentes: si una HU futura necesita contrib, el swap es directo y se
  actualiza este ADR.

## Decisión

**`opencv-python-headless` + `numpy` como dependencias de runtime**, declaradas con
floors permisivos y gobernadas por el lock:

- `pyproject.toml`: `opencv-python-headless>=4.10` · `numpy>=2.0`.
- `uv.lock` fija las exactas — hoy **OpenCV 5.0.0.93** y **NumPy 2.5.1** (hashes).
- Sin techo de versión: subir de mayor (4→5→6) es un evento **deliberado** de re-lock,
  re-verificado automáticamente por `tests/test_stack_vision.py` y, cuando existan, por
  los golden tests (cualquier cambio de píxel los rompe — esa es su función).

## Consecuencias

**Positivas**
- R-1 cerrado: stack de visión operativo en 3.13.2/Windows, sin fijar 3.12.
- El humo del stack corre en cada `pytest`: futuros updates del lock se auto-verifican.
- mypy estricto cubre `cv2` (stubs empaquetados) — sin excepciones de tipado.

**Negativas / mitigación**
- Sin `cv2.imshow` → debugging visual = export a archivo (coherente con el directorio de
  trabajo no destructivo).
- OpenCV 5 es reciente → el lock congela 5.0.0.93; regresión a 4.x sería un re-lock con
  floor ajustado, sin cambios de código esperados en `core`/`imgproc`.

**Neutrales / reglas derivadas**
- `core/` y `ranking/` siguen sin importar cv2/numpy-de-visión (regla `python.md`); la
  superficie de import queda en `vision/`, `photo/`, `video/`.
- Si alguna operación resultara no determinista por threading interno, `vision/` fija
  `cv2.setNumThreads(1)` para esa primitiva — el smoke y los golden tests son el detector.
- Los presupuestos de rendimiento por operación pertenecen a `benchmarks/` (HU-165), no a
  este ADR.
