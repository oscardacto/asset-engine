# Feedback — HU-012

## Anti-patrones detectados
- **Ordenar al serializar en vez de en el contrato.** La primera versión ordenaba las
  colecciones dentro de `save_catalog`, así que el objeto en memoria conservaba el orden de
  llegada y la ida y vuelta **no era fiel**: guardabas un catálogo y recuperabas otro
  distinto (igual en contenido, distinto en orden). El test lo detectó de inmediato.
  ADR-003 ya lo decía literalmente —"el orden es un dato, no un accidente de ejecución"—
  y yo lo había implementado como paso de serialización. **Si una propiedad es del dato,
  va en el constructor del dato.**

## Decisiones rechazadas
- **Rutas absolutas en el catálogo** — rechazadas: incrustarían `C:\Users\usuario\…` en cada
  entrada, romperían el determinismo entre máquinas y filtrarían el nombre de usuario a un
  archivo que puede compartirse.
- **Intentar leer un catálogo de versión desconocida "a ver si funciona"** — rechazado:
  produciría datos silenciosamente incompletos, que es peor que un error claro.
- **Escribir directamente sobre el archivo final** — rechazado por ADR-003: la escritura
  atómica es requisito, no optimización.
- **Guardar solo los aceptados** — rechazado: HU-018 debe reportar ambos y HU-013 no debe
  reintentar lo ya descartado.

## Lecciones aprendidas
- **Un test que simula el fallo vale más que un docstring que promete atomicidad.**
  `test_el_catalogo_anterior_sobrevive_a_un_fallo` interrumpe justo antes de sustituir y
  comprueba que el catálogo previo sigue entero. Sin él, "escritura atómica" sería una
  afirmación sin respaldo.
- **Nacer sobre la capa correcta cuesta cero.** Al implementarse después de HU-010, el
  catálogo usó `filesystem` desde la primera línea: ni una llamada directa al disco, y el
  test de gobernanza lo confirma. Migrar después habría costado un ciclo entero.
- **Las 7 HUs que construirán encima justificaron la versión desde v1.** Añadir `version`
  costó un campo; no tenerlo habría costado una migración cuando HU-035 sume su sección.
