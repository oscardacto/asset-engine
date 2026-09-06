# Reporte de QA — HU-104 · Crop 9:16 de material horizontal

> Fecha: 2026-09-06 · Rama: `feature/HU-104-crop-vertical` · Commit de DEV: `198a58d`

---

## 1. Evidencia contra los criterios de aceptación

| CA | Criterio | Prueba que lo verifica | Resultado |
|----|----------|------------------------|-----------|
| CA-1 | El filtro lleva las coordenadas calculadas | `test_el_filtro_lleva_las_coordenadas_calculadas` — literal `crop=1080:1920:1167:0` | ✅ |
| CA-2 | Las rutas se entregan adaptadas | `test_las_rutas_se_entregan_adaptadas` | ✅ |
| CA-3 | Un clip ya vertical no se recorta | `test_un_clip_ya_vertical_no_tiene_margen_que_desplazar` + `test_un_clip_ya_vertical_se_conserva` | ✅ |
| CA-4 | **El desplazamiento se queda dentro del cuadro** | 4 tests: mueve, mueve al otro lado, se acota por exceso, se acota a cero | ✅ |
| CA-5 | El original queda intacto | `test_el_original_queda_intacto` (bytes antes y después) | ✅ |
| CA-6 | La salida mide exactamente 1080×1920 | `test_la_salida_mide_exactamente_el_formato_vertical` | ✅ |
| CA-7 | Un clip ilegible aparta ese clip | 4 tests: roto, inexistente, sin medidas, herramienta que rechaza | ✅ |
| CA-8 | Funciona con rutas largas | `test_funciona_con_una_ruta_larga` (>260 caracteres) | ✅ |

**8/8 · 0 fallidos · sin rework.**

---

## 2. Los 23 tests, y por qué están repartidos así

| Grupo | Tests | Toca el binario |
|-------|------:|:---:|
| Comando de recorte | 5 | no |
| Desplazamiento y sus bordes | 6 | no |
| Clip que abre pero no mide | 1 | no |
| Sobre clips reales | 7 | sí |
| Degradación | 4 | sí |

**12 de 23 no ejecutan nada.** Construir el comando se separó de ejecutarlo a propósito: un
encuadre mal calculado se detecta comparando `crop=w:h:x:y` con valores literales, en
milisegundos, en vez de después de renderizar un lote.

---

## 3. Manejo de bordes acotados

El desplazamiento configurable **nunca se sale del material**. Cuatro pruebas fijan el
comportamiento en las dos direcciones:

| Petición | Margen real | Resultado |
|----------|------------:|-----------|
| `offset_x=200` | 2334 px | `crop=1080:1920:1367:0` — se aplica |
| `offset_x=-200` | 2334 px | `crop=1080:1920:967:0` — se aplica |
| `offset_x=99_999` | 2334 px | `crop=1080:1920:2334:0` — **acotado al margen** |
| `offset_x=-99_999` | 2334 px | `crop=1080:1920:0:0` — **acotado a cero** |
| `offset_x=500` sobre clip ya 9:16 | 0 px | `crop=1080:1920:0:0` — no hay margen que mover |

**Se acota en vez de fallar** porque un parámetro mal puesto convertiría un lote entero en
una interrupción a la mitad, y el encuadre acotado sigue siendo válido.

---

## 4. Ejecución de pruebas

```
tests/video/test_frame_cropping.py     23 passed
suite global                          803 passed, 1 skipped
```

| Módulo | Stmts | Miss | Cover |
|--------|------:|-----:|------:|
| `video/framing.py` | 37 | 0 | **100%** |
| **TOTAL del proyecto** | 2371 | 33 | **99%** |

`ruff check` ✅ · `ruff format --check` ✅ 133 files · `mypy src/` ✅ 58 source files.
`core/` sin tocar: el módulo vive en `video/`.

---

## 5. Validación con medios del cliente

```
2026-07-15-154529102.mp4    720x1280  -> 1080x1920   recorta_ancho=False   original intacto ✅
VID_20260726_165801.mp4    1080x1920  -> 1080x1920   recorta_ancho=False   original intacto ✅
VID_20260726_165817.mp4    1080x1920  -> 1080x1920   recorta_ancho=False   original intacto ✅
VID_20260726_165840.mp4    1080x1920  -> 1080x1920   recorta_ancho=False   original intacto ✅
```

**Los cuatro salen a 1080×1920 y los originales quedan byte a byte iguales.**

### El hallazgo del dominio

**El celular del cliente ya graba en 9:16 nativo.** Ninguno de sus clips recorta ancho — el
encuadre solo escala. La ruta de material apaisado está implementada y probada con clips
sintéticos (640×360, 4K, 1080p, 4:3), pero **hoy no se ejercita con el cliente 0**.

Esto tiene una consecuencia práctica: **la funcionalidad más costosa de esta HU es la que
menos se usa con el material actual**. Vale tenerlo presente antes de invertir en encuadre
inteligente — el problema que resolvería no aparece en este lote.

---

## 6. Dictamen

✅ **APROBADO PARA MERGE A `develop`.** Sin regresiones, sin deuda técnica nueva, sin
bloqueantes abiertos.
