# Reporte de QA — HU-102 · Score técnico por escena

| CA | Criterio | Prueba | Resultado |
|----|----------|--------|-----------|
| CA-1 | Escena bien expuesta puntúa más que oscura | `test_una_escena_bien_expuesta_puntua_mas_que_una_oscura` | ✅ |
| CA-2 | Cámara quieta puntúa más estable | `test_una_camara_quieta_puntua_mas_estable...` | ✅ |
| CA-3 | El muestreo no lee el clip entero | `test_no_se_leen_mas_cuadros_que_las_muestras_pedidas` | ✅ |
| CA-4 | El score es determinista | `test_es_determinista` | ✅ |
| CA-5 | Escena muy corta se puntúa igual | `test_una_escena_muy_corta_se_puntua_igual` | ✅ |
| CA-6 | Escena ilegible se aparta sin tumbar el clip | 2 tests (roto e inexistente) | ✅ |
| CA-7 | La nota promedia solo lo medido | `test_anadir_un_componente_no_cambiaria_el_contrato` | ✅ |

**7/7 · 0 fallidos · 1 rework interno a la HU (ver abajo).**

## Ejecución

```
tests/core/test_scene_score.py      10 passed
tests/video/test_scene_scoring.py   21 passed
suite global                       752 passed, 1 skipped
```

| Módulo | Cover |
|--------|------:|
| `core/scene_score.py` | **100%** |
| `video/scene_scoring.py` | **98%** — la línea sin cubrir es el caso en que ningún cuadro tiene contiguo, inalcanzable con clips válidos |
| TOTAL | **99%** |

`ruff check` ✅ · `ruff format --check` ✅ 129 files · `mypy src/` ✅ 56 source files.

## Validación con material real (7 videos del cliente, 19 escenas)

| | Antes de la corrección | Después |
|---|---|---|
| Valores distintos de estabilidad | prácticamente 1 | **10 de 19** |
| Rango observado | casi todo 0.000 | 0.000 – 0.404 |

Mejor escena medida: `exposure=0.928 stability=0.404` · Peor: `exposure=0.799 stability=0.000`.

## Alcance recortado, con motivo

**Nitidez fuera.** HU-023 es un `ADR` sin cerrar que decide cómo medirla (varianza de
Laplaciano frente a Tenengrad) y no está iniciada. El backlog además **no la declara como
dependencia de HU-102** — inconsistencia anotada, no resuelta aquí. El contrato deja el hueco
preparado: la nota general promedia los componentes disponibles.

## Dictamen

✅ **APROBADO PARA MERGE A `develop`.** Sin regresiones, sin bloqueantes abiertos.
