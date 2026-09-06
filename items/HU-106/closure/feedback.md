# Feedback — HU-106

## Lecciones aprendidas

- **«Exacto» es un requisito de tipo de dato, no de esfuerzo.** El enunciado pedía cumplir
  exactamente una duración objetivo, y en coma flotante eso es literalmente inalcanzable:
  medido, el recorte proporcional da 15.000000000000002. Ningún cuidado al escribir la
  fórmula lo arregla — hay que cambiar de aritmética. **Cuando un requisito diga «exacto»,
  «idéntico» o «byte a byte», la primera pregunta es en qué tipo se está calculando.**
  Es el mismo problema que HU-168 resolvió separando lo medido de lo reproducible, y que
  ADR-003 resolvió ordenando las claves del JSON.

- **Un test que demuestra que el método descartado falla vale tanto como el que prueba el
  elegido.** `test_el_calculo_ingenuo_en_coma_flotante_no_habria_cerrado` no prueba el código
  de producción: prueba que el problema existe. Sin él, el test de exactitud podría pasar por
  casualidad sobre datos benignos y nadie sabría que la aritmética entera está haciendo algo.
  Es la misma idea que verificar los guardianes por inyección, aplicada a una decisión de
  implementación.

- **No alargar es una decisión de producto, no una limitación.** Si las escenas suman 9 s y
  se piden 15, se podría repetir cuadros o ralentizar. Pero eso **cambia lo que se ve**: es
  una transformación del contenido disfrazada de ajuste de duración. La función informa que
  no alcanzó y devuelve la decisión a quien llama. **Una función que silenciosamente inventa
  lo que le falta es peor que una que avisa.**

- **Se adelantó a su dependencia declarada sin romper nada.** El backlog cuelga HU-106 de
  HU-105, que está bloqueada por HU-032. Pero el núcleo del recorte opera sobre `Scene` y no
  necesita el guion: la dependencia era de *orden de uso*, no de *código*. Distinguir las dos
  cosas permitió no dejar la épica parada.

## Decisiones rechazadas

- **Calcular en segundos con decimales** — es lo natural y no cumple el requisito. Medido.
- **Repartir el residuo entre todas las escenas** — un milisegundo dividido entre tres no es
  divisible en enteros, así que el problema vuelve. Va entero a una sola: es imperceptible a
  treinta cuadros por segundo.
- **Alargar el material corto repitiendo cuadros** — inventa contenido; ver arriba.
- **Una sola estrategia de recorte** — «conservar todo el recorrido» y «conservar bien lo
  mejor» son objetivos distintos, y el perfil decidirá cuál aplica. Hay un test que comprueba
  que producen resultados distintos, para que no converjan por descuido.
- **Recortar por el centro de cada escena** — se conserva el principio, que es donde suele
  estar el encuadre estable de una toma. Cambiarlo sería añadir un parámetro de anclaje, y no
  hay evidencia de que haga falta.

## Anotado

`MINIMO_POR_ESCENA` está en 1 segundo. Es un punto de partida razonable —una toma más breve
en un reel es un parpadeo— pero **no está calibrado con material real**, a diferencia de los
umbrales de HU-103. Cuando HU-133 fije los datos del perfil, conviene revisarlo junto al
umbral de duración de descarte (1,5 s), con el que guarda relación evidente.
