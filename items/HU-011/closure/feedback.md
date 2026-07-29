# Feedback — HU-011

## Anti-patrones detectados
- **Test que verificaba lo que creía verificar, pero por otro motivo.** El primer intento
  de "archivo cuyas dimensiones no se pueden leer" corrompía los bytes 2-4 del JPEG… lo que
  rompía también la **firma**, así que el triaje lo rechazaba por formato desconocido mucho
  antes de llegar al chequeo de dimensiones. El test fallaba por la razón correcta pero
  probaba lo equivocado. **Al construir un caso negativo, verificar que falla en el paso que
  se quiere probar y no en uno anterior.**
- **Segunda rama muerta en dos HUs consecutivas.** `_is_truncated` usaba `.get()` con
  fallback a `None` para un formato sin marca de cierre — imposible, porque WebP se trata
  antes y los otros dos soportados sí la tienen. Se sustituyó por acceso directo: un
  `KeyError` ruidoso en desarrollo es mejor que aceptar archivos a ciegas en producción.
  Patrón a vigilar: **el fallback defensivo que "no puede pasar" suele ser código muerto.**

## Decisiones rechazadas
- **Un umbral en píxeles "que suenan muchos"** — rechazado por dato: el celular de
  referencia del cliente 0 tiene sensor de 200 MP, y el aviso por defecto de Pillow salta
  a los ~89 MP. Un umbral intuitivo habría descartado fotos reales del cliente. El límite
  se expresa en **memoria estimada** y hay un test que exige que 200 MP se acepten.
- **Implementar solo la variante WebP con pérdida** — rechazado tras verificar los bytes:
  nuestro propio cv2 produce **VP8L** (sin pérdida). La suposición natural habría fallado
  contra nuestros propios fixtures.
- **Apartar los archivos cuyas dimensiones no se pueden leer** — rechazado (fail-safe,
  coherente con la política de truncamiento de HU-009): no se descarta material por no
  poder medirlo; si además fuera una bomba, la decodificación lo detectará.
- **Estimar el pico real de memoria del decodificador** — rechazado: depende del códec y
  de la implementación. La estimación del bitmap es una cota inferior honesta, declarada
  como tal; el presupuesto real es de HU-165.

## Lecciones aprendidas
- **Un umbral de seguridad se calibra con el dispositivo del cliente, no con el sentido
  común.** Este fue el caso más claro hasta ahora de que el charter (§6.7, dispositivo de
  referencia) contiene información que cambia decisiones técnicas concretas. Vale la pena
  releerlo al fijar cualquier límite.
- **Verificar el formato real antes de escribir el parser** volvió a pagar, igual que en
  HU-002: cinco minutos inspeccionando bytes evitaron implementar la variante equivocada.
- **La cobertura sigue funcionando como detector de diseño, no de tests faltantes.** Las
  dos líneas sin cubrir eran: una rama alcanzable sin probar (JPEG malformado, se añadió
  test) y una rama imposible (se borró). Ninguna de las dos se resolvía "escribiendo más
  tests" sin pensar.
- **Ampliar el registro de cuarentena de HU-009 costó una línea de enum.** La afirmación
  de que el mecanismo era extensible quedó demostrada por su primer consumidor real.
