# Reporte de QA — HU-106 · Recorte de escenas a duración objetivo

> Fecha: 2026-09-06 · Rama: `feature/HU-106-recorte-duracion`

---

## 1. Evidencia contra los criterios de aceptación

| CA | Criterio | Prueba que lo verifica | Resultado |
|----|----------|------------------------|-----------|
| CA-1 | **El recorte proporcional cierra al milisegundo** | `test_el_recorte_proporcional_cierra_al_milisegundo` + 5 metas parametrizadas | ✅ |
| CA-2 | Quitar del final conserva las primeras enteras | `test_las_primeras_conservan_su_duracion_natural` | ✅ |
| CA-3 | Material más corto no se alarga | 2 tests, uno por estrategia | ✅ |
| CA-4 | Material que ya suma la meta no se toca | `test_material_que_ya_suma_la_meta_no_se_toca` | ✅ |
| CA-5 | Una escena que quedaría un parpadeo se descarta | 4 tests del mínimo por escena | ✅ |
| CA-6 | El plan dice qué quedó fuera | `test_informa_que_escenas_quedaron_fuera` | ✅ |
| CA-7 | El ajuste es determinista | `test_el_mismo_lote_y_meta_dan_el_mismo_plan` | ✅ |
| CA-8 | Una meta imposible falla al pedirla | 3 tests (meta cero, negativa, mínimo cero) | ✅ |

**8/8 · 0 fallidos · sin rework.**

---

## 2. La precisión, que era el motivo del diseño

El test que sostiene toda la HU compara las dos aritméticas sobre el mismo caso:

```
cálculo ingenuo en coma flotante:  12.4·f + 20.1·f + 14.8·f  =  15.000000000000002
recorte con aritmética entera:                                  15.0   exacto
```

Hay un test dedicado —`test_el_calculo_ingenuo_en_coma_flotante_no_habria_cerrado`— que
**afirma que el método descartado falla**. Sin él, el test de exactitud podría pasar por
casualidad sobre datos benignos y nadie sabría que la aritmética entera está haciendo algo.

Verificado además para 5 metas distintas: 15, 30, 60, 7.5 y 22.333 segundos. Todas cierran.

---

## 3. Las dos estrategias hacen cosas distintas

| Sobre tres escenas de 6 s, meta 15 s | Resultado |
|---|---|
| **Proporcional** | tres escenas de 5 s — aparece todo el recorrido, más breve |
| **Quitar del final** | 6 s + 6 s + 3 s — las dos primeras salen con su duración natural |

Ambas suman exactamente 15. Hay un test que comprueba que **producen resultados distintos**:
si alguien las hiciera converger, dejaría de haber dos estrategias.

---

## 4. Ejecución de pruebas

```
tests/core/test_scene_trimmer.py      32 passed
suite global                         835 passed, 1 skipped
```

| Módulo | Stmts | Miss | Cover |
|--------|------:|-----:|------:|
| `core/scene_trimmer.py` | 74 | 0 | **100%** |
| **TOTAL del proyecto** | 2446 | 33 | **99%** |

`ruff check` ✅ · `ruff format --check` ✅ · `mypy src/` ✅ 59 source files.

---

## 5. Pureza hexagonal

`scene_trimmer.py` importa **solo** `dataclasses`, `enum` y `Scene`. Sin ffmpeg, sin OpenCV,
sin IO, sin la librería de escenas. El test de arquitectura sobre `core/` sigue en verde.

---

## 6. Un test que se reforzó durante el cierre

`test_el_tiempo_de_la_descartada_se_reparte` tenía una aserción con `or` que habría pasado
aunque el reparto no ocurriera. Se midió el comportamiento real —descarta la escena 2 y deja
dos de 15 s exactos— y se fijaron esos valores. **Una aserción con `or` es una que puede
pasar sin comprobar nada.**

---

## 7. Dictamen

✅ **APROBADO PARA MERGE A `develop`.** Sin regresiones, sin deuda técnica nueva, sin
bloqueantes abiertos.
