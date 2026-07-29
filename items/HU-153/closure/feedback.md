# Feedback — HU-153

## Anti-patrones detectados
- **Estuve a punto de escribir en la spec una afirmación falsa con tono de certeza.** La
  hipótesis inicial era "SQLite no es reproducible byte a byte porque el formato binario
  arrastra estado". Al medirlo, el caso simple resultó **idéntico** — la afirmación general
  era falsa. Solo el escenario realista (orden de inserción distinto, construcción
  incremental) mostró la divergencia. Si se hubiera escrito la intuición como hecho, el ADR
  habría quedado apoyado en un argumento que cualquiera puede refutar en 30 segundos, y la
  decisión correcta habría tenido una justificación equivocada. **Medir antes de afirmar,
  incluso cuando la conclusión final no cambia.**

## Decisiones rechazadas
- **SQLite** — rechazado no por rendimiento ni complejidad, sino porque rompe el criterio
  dominante: produce archivos distintos ante el mismo contenido lógico en los dos
  escenarios que genera una re-ingesta. Además exige un cliente SQL para inspeccionarlo, lo
  que degrada el requisito de "catálogo consultable con las herramientas del repo".
- **JSONL append-only** — rechazado: la idempotencia exigiría compactar, y la compactación
  reintroduce el problema de orden que se quería evitar; además el estado actual de un asset
  obligaría a reconstruir todo el historial.
- **Decidir por "menos dependencias"** — descartado como criterio: `json` y `sqlite3` están
  **ambos** en la stdlib, así que no desempata. Merecía decirlo explícitamente en el ADR
  para que nadie lo invoque después como razón retroactiva.
- **Dejar la reconsideración a criterio futuro** — rechazado: el ADR lista tres disparadores
  concretos, de modo que revisarlo sea una decisión con umbral y no una discusión de gustos.

## Lecciones aprendidas
- **El criterio dominante de un ADR no siempre es el que la pregunta sugiere.** El ticket
  planteaba "JSON vs SQLite", que suena a decisión de escalabilidad; el charter la convierte
  en una decisión de reproducibilidad. Leer las restricciones antes que las alternativas
  cambia cuál es la pregunta.
- **Cerrar los tres ADRs de stack antes de que el código dependa de ellos funcionó.** Ningún
  WorkItem ha tenido que rehacerse por una decisión de stack tardía: uv, OpenCV y ahora el
  catálogo se decidieron con su HU y su evidencia, cada uno antes de su primer consumidor.
- **La tabla de stack de CLAUDE.md ya no tiene filas "ADR pendiente"**, que era un indicador
  visible de deuda de arquitectura. Vale la pena mantener ese tipo de marcador explícito en
  la constitución: hace la deuda imposible de olvidar.
