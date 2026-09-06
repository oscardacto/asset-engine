# Reporte de QA — HU-101 · Detección de escenas

> Fecha: 2026-09-06 · Rama: `feature/HU-101-deteccion-escenas` · Commit de DEV: `956335b`

---

## 1. Evidencia contra los criterios de aceptación

| # | Criterio (de la spec) | Prueba que lo verifica | Resultado |
|---|----------------------|------------------------|-----------|
| CA-1 | Un clip con un corte produce dos escenas | `test_un_clip_con_un_corte_produce_dos_escenas` | ✅ |
| CA-2 | Un clip sin cortes produce **una** escena, no cero | `test_un_clip_sin_cortes_produce_una_sola_escena` | ✅ |
| CA-3 | Las escenas salen en orden y sin solaparse | `test_las_escenas_salen_en_orden_y_sin_solaparse` | ✅ |
| CA-4 | Mismo clip y umbral ⇒ mismas escenas | `test_el_mismo_clip_da_siempre_las_mismas_escenas` | ✅ |
| CA-5 | Un umbral más bajo no encuentra menos cortes | `test_un_umbral_mas_bajo_no_encuentra_menos_cortes` | ✅ |
| CA-6 | **Funciona con rutas largas** (hallazgo H-2) | `test_funciona_con_una_ruta_larga` (>260 car.) | ✅ |
| CA-7 | Un clip ilegible aparta ese asset, no tumba el lote | `test_un_clip_ilegible_degrada_ese_asset` | ✅ |
| CA-8 | Un clip inexistente aparta ese asset | `test_un_clip_inexistente_degrada_ese_asset` | ✅ |
| CA-9 | El adaptador cumple el puerto del dominio | `test_el_adaptador_cumple_el_puerto` | ✅ |
| CA-10 | **Ninguna estructura de la librería sale al dominio** | `test_ninguna_estructura_de_la_libreria_sale_del_adaptador` | ✅ |
| CA-11 | El adaptador es inmutable | `test_el_adaptador_es_inmutable` | ✅ |
| CA-12 | Umbral por defecto declarado | `test_el_umbral_por_defecto_esta_declarado` | ✅ |

**12/12 · 0 fallidos · sin rework.**

---

## 2. Ejecución de pruebas

```
tests/video/test_scenedetect_adapter.py    12 passed
tests/core/test_scene.py                   10 passed
tests/video/ (completo)                    94 passed, 0 failed, 0 xfailed, 0 skipped
suite global                              721 passed, 1 skipped
```

El único omitido de toda la batería es `test_filesystem.py:50` — comportamiento POSIX en
máquina Windows, ajeno a esta HU.

### Trazabilidad del ciclo TDD

Los 8 tests de detección se escribieron **antes** que la implementación, en `xfail(strict=True)`.
Al implementar el adaptador pasaron a verde y el modo estricto **obligó a desmarcarlos**: si se
hubieran dejado, habrían fallado por pasar. Esa es la evidencia de que el ciclo rojo → verde
ocurrió de verdad y no se escribieron los tests después del código.

---

## 3. Cobertura

| Módulo | Stmts | Miss | Cover |
|--------|------:|-----:|------:|
| `video/scenedetect_adapter.py` | 28 | 0 | **100%** |
| `core/scene.py` | 20 | 0 | **100%** |
| `core/ports/scene_detector.py` | 5 | 0 | **100%** |
| `core/ports/__init__.py` | 2 | 0 | **100%** |
| **TOTAL del proyecto** | 2200 | 32 | **99%** |

Cumple el objetivo: ≥98% global, 100% en el adaptador y en `core/`.

---

## 4. Verificación estática

| Comprobación | Resultado |
|---|---|
| `ruff check .` | ✅ All checks passed |
| `ruff format --check .` | ✅ 124 files already formatted |
| `mypy src/` (estricto) | ✅ Success — 54 source files |

El único silencio de tipos es la importación de `scenedetect`, que no publica tipos. Está
acotado a esa librería en `pyproject.toml`: lo que entra y sale del adaptador sigue tipado en
estricto, y el dominio nunca la ve.

---

## 5. Verificación de aislamiento hexagonal

| Comprobación | Resultado |
|---|---|
| `scenedetect` importado solo en `video/scenedetect_adapter.py` | ✅ |
| `cv2` fuera de `core/` | ✅ (test de arquitectura) |
| `core/` no importa `media_optimizer.video` | ✅ (test de arquitectura) |
| El puerto solo usa `Path`, `Protocol` y `Scene` | ✅ |
| El adaptador devuelve `Scene`, nunca estructuras ajenas | ✅ CA-10 |

---

## 6. Los dos hallazgos medidos, y qué evitaron

**H-1 · Conflicto de empaquetado.** `scenedetect` declara la variante de OpenCV con interfaz
gráfica; ADR-002 eligió la variante sin interfaz. Ambas instalan el mismo módulo en el mismo
directorio. Al medirlo, el entorno de prueba acabó con ese módulo inservible. Resuelto con un
override verificado en el proyecto real. **Sin la medición previa, esto habría aparecido como
un fallo intermitente de importación, difícil de atribuir.**

**H-2 · Rutas largas.** La librería no encuentra un video cuya ruta supera los 260 caracteres
si se le entrega tal cual. Es el tercer caso del mismo patrón en el proyecto, tras el
manejador de archivos de la biblioteca estándar y la herramienta de video. Cubierto por CA-6.

**Hallazgo adicional durante DEV:** la librería devuelve **lista vacía** cuando no hay cortes,
no una escena. Sin normalizarlo, un clip continuo habría producido cero escenas y
**desaparecido del reel en silencio**. Cubierto por CA-2.

---

## 7. Dictamen

✅ **APROBADO PARA MERGE A `develop`.**

Sin regresiones, sin deuda técnica nueva, sin bloqueantes abiertos.
