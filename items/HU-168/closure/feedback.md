# Feedback — HU-168

## Lecciones aprendidas

- **Cuando dos reglas del proyecto se contradicen, la solución es un tipo, no una
  convención.** El mandato de observabilidad y la promesa de determinismo chocan de frente:
  hay que reportar tiempo, y el tiempo no se reproduce. Documentar "no metas el reporte
  completo en un golden test" habría durado hasta el primer despiste. Un tipo distinto
  (`ReproducibleStageSummary`) hace que el error no compile. **Vale para el resto del
  proyecto: donde una regla dependa de que alguien se acuerde, probablemente falte un tipo.**

- **Una separación hay que probarla en las dos direcciones o no prueba nada.** El test de
  "tiempos distintos comparan igual" lo pasaría también una implementación que devolviera
  siempre el mismo objeto vacío. Hizo falta el test simétrico —"transformaciones distintas
  comparan distinto"— para que el par signifique algo. Es la misma lección que dejó HU-160
  al inyectar la violación en el guardián de generalización: **una prueba que solo puede
  pasar no es una prueba**; en dos HUs seguidas apareció la misma forma de falso verde.

- **El fallo que se evitó habría sido caro justamente por ser leve.** Un golden test que
  falla 1 de cada 100 corridas mostrando `0.031` contra `0.029` no se lee como un defecto de
  diseño: se lee como ruido, se re-ejecuta, pasa, y se olvida. Los errores intermitentes
  cuestan más que los deterministas aunque su impacto sea menor.

## Decisiones rechazadas
- **Redondear la duración para meterla en la parte comparable** — no vuelve determinista un
  tiempo, solo hace la intermitencia más rara. Un dato es reproducible o no lo es.
- **Medir dentro de `core/`** — `perf_counter` y `tracemalloc` son impuros; el dominio recibe
  lo medido. Medir es de HU-180.
- **Añadir conteos del run al contrato** — el mandato son cuatro campos y los conteos son de
  run, no de etapa (HU-183). Mismo criterio de alcance que en HU-016 y HU-160.
- **Memoria en MiB** — metería un float y un redondeo entre la medida y el dato; presentarlo
  legible es de HU-181.
