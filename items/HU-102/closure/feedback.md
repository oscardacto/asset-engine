# Feedback — HU-102

## El defecto que solo apareció con material real

La estabilidad comparaba las muestras entre sí, separadas por alrededor de un segundo. Con
clips sintéticos el test pasaba —un clip gris quieto daba 1.0 y uno con `testsrc2` daba
0.76— así que la métrica parecía funcionar. **Sobre los 7 videos del cliente dio 0.000 en
casi todas las escenas.**

Causa raíz: dos cuadros a un segundo de distancia en un recorrido de apartamento difieren
muchísimo aunque la cámara esté perfectamente firme. Se estaba midiendo **paneo acumulado**,
no temblor. Corregido a comparar cada cuadro con el contiguo.

**La lección no es sobre video.** Los fixtures sintéticos confirmaron que la función devolvía
números distintos para entradas distintas, que es lo que un test unitario puede comprobar.
Lo que no podían comprobar es si esos números **significan** algo en el dominio real: una
métrica que da 0 a casi todo sigue pasando un test de dos casos si esos dos casos están
suficientemente separados. **Toda métrica nueva necesita una pasada por material real antes
de darse por buena, y el criterio de aceptación es que sus valores se repartan — no que la
función corra.**

Es el segundo caso del mismo tipo en el proyecto: en HU-004, `Orientation=0` se trataba como
EXIF corrupto y solo el lote real de 82 fotos lo destapó.

## Decisiones rechazadas

- **Implementar la nitidez aquí** — cerraría el ADR de HU-023 sin escribirlo. El enunciado la
  pide y el backlog no declara la dependencia: la inconsistencia se anota, no se resuelve
  saltándose la gobernanza.
- **Subir el umbral de referencia en vez de cambiar la medida** — habría maquillado el
  síntoma. El problema era **qué** se comparaba, no con qué se comparaba.
- **Recorrer el clip para muestrear** — el charter prohíbe cargar video completo a RAM.
- **Penalizar la escena cuando no hay cuadro contiguo** — no se castiga lo que no se pudo
  observar; se devuelve estabilidad perfecta y el número de cuadros mirados queda registrado.

## Anotado para HU-133

El rango de estabilidad sobre material real llega solo a 0.404: la referencia de 12 niveles
sigue siendo estricta para video de celular a pulso. Ahora la métrica **discrimina**, que es
lo que hacía falta para poder calibrarla; dónde cae el corte lo fija el perfil.
