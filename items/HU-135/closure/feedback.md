# Feedback — HU-135

## Incumplimiento de proceso — la lección principal

**La HU se implementó, se integró a `develop` y se marcó DONE sin spec, sin gate y con la
mitad de sus artefactos ausentes.** Lo detectó una auditoría posterior, no el propio ciclo.

Causa raíz: se venía trabajando en Modo Ejecución con la instrucción de no generar
documentación innecesaria, y eso se aplicó también a los artefactos que **no son
documentación sino evidencia de gobernanza**. El gate-log y la spec no son prosa: son lo que
impide que "pasó los tests" sustituya a "se aprobó su especificación".

**Regla que sale de aquí: la velocidad puede recortar la prosa explicativa, nunca el registro
del gate.** Un `gate_spec` en el gate-log son dos líneas y treinta segundos; su ausencia
invalida la trazabilidad de todo lo que vino después.

La regularización deja los eventos marcados con `regularizacion_post_merge: true`. No se
presentan como si se hubieran emitido a tiempo — falsificar la fecha habría convertido un
error de proceso en un error de integridad, que es mucho peor.

## Lecciones técnicas

- **El caso más tentador de romper la regla de generalización es el que tiene nombres
  bonitos.** Un guion con tramos llamados "fachada", "umbral", "cocina" pide a gritos ser un
  enumerado: son pocos, son estables y leen bien. Pero son criterio de un cliente. El test
  del bar nocturno es lo que convierte la regla en algo verificable.

- **Ante la falta de material, la respuesta útil no es la completa.** Rellenar el guion
  produce un reel que se ve entero y miente sobre la cobertura. Dejar el hueco produce menos
  video y más información — y esa información *es* el entregable de otra HU.

- **Pasar las etiquetas como mapping aparte evitó acoplar `ranking/` a los ambientes.**
  Añadir un campo a `RankedAsset` habría sido más cómodo y habría hecho que el dominio del
  ranking supiera de algo que no le corresponde.

## Decisiones rechazadas

- **Slots como enumerado cerrado** (`slot_facade`, `slot_interior`, `slot_detail`) — es
  criterio de cliente en el código; el charter §3 lo prohíbe.
- **Rellenar los huecos con los mejores clips libres** — oculta lo que falta grabar.
- **Añadir `setting` a `RankedAsset`** — acopla el ranking a un concepto que no es suyo.
- **Un tramo con varios clips** — sin consumidor todavía; `SlotAssignment` puede pasar a una
  tupla de forma aditiva cuando HU-105 lo pida.
