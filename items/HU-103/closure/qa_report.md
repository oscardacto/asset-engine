# Reporte de QA — HU-103 · Descarte de escenas con causas

> Fecha: 2026-09-06 · Rama: `feature/HU-103-descarte-escenas` · Commit de DEV: `a491078`

---

## 1. Evidencia contra los criterios de aceptación

| CA | Criterio | Prueba que lo verifica | Resultado |
|----|----------|------------------------|-----------|
| CA-1 | Una escena buena se conserva sin causas | `test_una_escena_buena_pasa_sin_causas` | ✅ |
| CA-2 | Una escena corta se descarta por duración | `test_una_escena_corta_se_descarta_por_duracion` | ✅ |
| CA-3 | Una escena temblorosa se descarta por estabilidad | `test_una_escena_temblorosa_se_descarta_por_estabilidad` | ✅ |
| CA-4 | Se reportan **todas** las causas, no la primera | `test_se_reportan_todas_las_causas_no_la_primera` + orden estable | ✅ |
| CA-5 | El umbral es el mínimo aceptable | `test_el_umbral_es_el_minimo_aceptable_no_el_primer_rechazo` | ✅ |
| CA-6 | **El juicio no depende de la nota general** | 2 tests: misma nota → veredictos distintos; nota alta no salva componente hundido | ✅ |
| CA-7 | Un lote entero descartado es válido | `test_un_lote_entero_descartado_es_un_resultado_valido` | ✅ |
| CA-8 | **Los umbrales por defecto no vacían el material real** | 3 tests contra los valores medidos del cliente | ✅ |

**8/8 · 0 fallidos · sin rework.**

---

## 2. Ejecución de pruebas

```
tests/core/test_scene_selector.py     28 passed
suite global                         780 passed, 1 skipped
```

El único omitido de toda la batería es `test_filesystem.py:50` — comportamiento POSIX en
máquina Windows, ajeno a esta HU.

| Módulo | Stmts | Miss | Cover |
|--------|------:|-----:|------:|
| `core/scene_selection.py` | 48 | 0 | **100%** |
| **TOTAL del proyecto** | 2333 | 33 | **99%** |

---

## 3. Verificación estática

| Comprobación | Resultado |
|---|---|
| `ruff check .` | ✅ All checks passed |
| `ruff format --check .` | ✅ 131 files already formatted |
| `mypy src/` (estricto) | ✅ Success — 57 source files |

---

## 4. Pureza del dominio

`scene_selection.py` importa **solo** `dataclasses`, `enum` y los contratos `Scene` y
`SceneScore`. Sin ffmpeg, sin OpenCV, sin la librería de detección de escenas. El test de
arquitectura sobre `core/` sigue en verde.

---

## 5. Validación con material real (7 videos, 19 escenas)

```
2026-07-15-154529102.mp4     5/13 conservadas
VID_20260726_165801.mp4      1/ 1
VID_20260726_165817.mp4      0/ 1
VID_20260726_165840.mp4      1/ 1
VID_20260726_165853.mp4      1/ 1
VID_20260726_165911.mp4      0/ 1
VID_20260726_165927.mp4      0/ 1

TOTAL: 8 conservadas de 19 escenas (42%)
causas: too_short 5 · unstable 10 · poor_exposure 0
```

**Los umbrales se comportan como debían:** ni vacían el lote ni lo dejan pasar entero. Y
ninguna escena cae por exposición, que es lo correcto — el material del cliente va de 0.799 a
0.976 de exposición; su problema es el pulso, no la luz.

---

## 6. Las dos propiedades que este cierre garantiza a futuro

**El juicio no se romperá cuando entre la nitidez.** HU-102 dejó anotado que la nota general
promedia solo los componentes disponibles y cambiará de valor al sumar uno nuevo. Los
umbrales van por componente, y CA-6 lo fija con dos pruebas: si alguien mueve el criterio a
la nota general, esas pruebas fallan.

**No se puede construir un veredicto incoherente.** `keep` se deriva de `reasons` en vez de
guardarse aparte, así que no existe forma de marcar como buena una escena que traiga motivos
de descarte. Hay un test que comprueba que `keep` no figura entre los campos asignables.

---

## 7. Dictamen

✅ **APROBADO PARA MERGE A `develop`.** Sin regresiones, sin deuda técnica nueva, sin
bloqueantes abiertos.
