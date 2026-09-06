# Feedback — HU-070+071+072+074+078+180+184

## Lecciones
- **`run all` no necesitó orquestador nuevo**: la secuencia reutiliza `execute_stage`, que
  ya existía. HU-180 pedía "un asset que falla degrada, el lote continúa" y eso ya estaba
  resuelto dentro de cada etapa; lo único que faltaba era propagar el `partial` hacia
  arriba. El diseño de etapas-como-datos evitó escribir un orquestador de verdad.
- **La plantilla narrativa se entregó como lo que hoy se puede sostener**, no como lo que
  el backlog aspira: gancho + alternancia de orientación. La versión por ambientes exige
  HU-032 y E6; prometerla ahora habría sido un `gallery_order` que finge conocer ambientes
  que nadie etiquetó.

## Decisiones rechazadas
- **Cerrar HU-073 (cobertura de ambientes en la selección)** — depende de ambientes que no
  existen. Queda abierta.
- **Ponderar el score con pesos por intención ya** — es HU-134, datos del perfil. Hoy hay
  un peso único con `TODO(HU-134)`.
