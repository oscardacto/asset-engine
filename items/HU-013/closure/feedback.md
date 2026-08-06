# Feedback — HU-013

## Anti-patrones detectados
- (Ninguno en ejecución. Segunda HU consecutiva verde a la primera; la única corrección fue
  ruff reordenando `__all__`, que es automática.)

## Decisiones rechazadas
- **Comparar por ruta** — rechazado por ADR-004 §1: la identidad es el contenido. Comparar
  por ruta habría hecho que renombrar una foto la convirtiera en otra.
- **Tratar el renombrado como alta + baja** — rechazado, y es la decisión central de la HU:
  HU-019 perdería las etiquetas manuales del usuario solo porque movió la foto de carpeta.
- **Persistir el plan** — rechazado: es estado derivado; guardarlo crea una segunda fuente
  de verdad que puede desincronizarse del catálogo.
- **Exponer una comparación por ruta "por si acaso"** — rechazado: la API solo devuelve el
  plan ya calculado, de modo que ningún consumidor pueda tomar el atajo equivocado.

## Lecciones aprendidas
- **Un ticket de una línea puede esconder un caso que no nombra.** "No duplica ni reprocesa"
  parecen dos exigencias; son tres. El renombrado no está en ninguna de las dos palabras y
  es justo el que, mal resuelto, causa la pérdida de datos del usuario. Vale la pena
  preguntarse, ante cualquier comparación de estados, **qué pasa cuando algo se mueve**.
- **La decisión de identidad tomada en ADR-004 se cobró aquí.** No hubo que discutir si
  comparar por hash o por ruta: ya estaba decidido y escrito. Las decisiones de arquitectura
  bien ubicadas ahorran deliberación en las HUs que vienen después.
- **Que la HU no toque disco es consecuencia de un buen límite.** Compara dos catálogos ya
  cargados; quién los lee es de otra capa. Eso la hace trivialmente testeable —14 tests sin
  un solo archivo temporal— y explica su 100% de cobertura.
