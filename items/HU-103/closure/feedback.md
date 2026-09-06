# Feedback — HU-103

## Lecciones aprendidas

- **Un umbral que suena razonable en abstracto puede vaciar el lote entero.** Sin la medición
  que HU-102 dejó anotada, el mínimo de estabilidad se habría fijado en algo como 0.5 — un
  número que en una escala de 0 a 1 parece permisivo. La estabilidad real del material del
  cliente llega **como máximo a 0.404**, así que ese umbral habría descartado las 19 escenas
  y el pipeline habría devuelto un reel vacío sin que ningún test lo detectara. **Ningún
  umbral entra sin haber visto la distribución real de la métrica sobre la que se aplica.**

- **El HANDOFF pagó su coste en la primera HU que lo usó.** Los tres avisos que dejó HU-102
  —el tope de 0.404, que la nota general cambiará de valor, y que las escenas de menos de
  1,5 s son paneo— se convirtieron directamente en los tres umbrales y en la decisión de
  arquitectura de esta HU. Sin ellos habría hecho falta volver a medir o, peor, adivinar.

- **La causa es el entregable, no el veredicto.** Decidir esto al principio cambió el diseño:
  se reportan *todas* las causas en vez de cortar en la primera. Un descarte que dice «esta
  toma no sirve» obliga al usuario a adivinar; uno que dice «quedó corta **y** con pulso» le
  dice exactamente qué repetir. El coste fue nulo — recorrer las tres comprobaciones en vez
  de salir antes.

- **Derivar `keep` de `reasons` elimina un estado imposible.** Guardarlo como campo aparte
  habría permitido construir un veredicto que se conserva y a la vez trae motivos de
  descarte. Es el mismo criterio que en HU-168 separó lo medido de lo reproducible con un
  tipo distinto: **donde una regla dependa de que alguien se acuerde, probablemente falte una
  derivación o un tipo.**

## Decisiones rechazadas

- **Un umbral sobre la nota general** — es lo más corto de escribir y lo que se rompería solo
  el día que entre la nitidez, sin que nadie tocara nada y sin ningún test que avisara.
- **Devolver solo la primera causa** — más simple, y pierde justo el valor del descarte.
- **Fijar los umbrales por intuición** — habría vaciado el lote; ver arriba.
- **Levantar una excepción cuando todo el lote se descarta** — un lote mal grabado es un
  resultado normal del dominio, no un fallo del programa. Lo que corresponde es informarlo
  con sus causas.
- **Añadir una causa de «poco nítida»** — la métrica no existe todavía: HU-023 es un `ADR`
  sin cerrar. El enumerado admite el valor nuevo de forma aditiva cuando llegue.

## Anotado para HU-133

Con los umbrales actuales sobrevive el **42%** del material real (8 de 19 escenas), y el
único criterio que descarta es la estabilidad (10 casos) junto con la duración (5). La
exposición no aparta nada. Cuando HU-133 calibre con el perfil, ese reparto es el punto de
partida medido: si el negocio quiere conservar más, el parámetro a mover es la estabilidad.
