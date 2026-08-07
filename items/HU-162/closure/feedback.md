# Feedback — HU-162

## Anti-patrones detectados

- **Reexportar una función con el nombre de su propio módulo lo vuelve inalcanzable.**
  `cli/__init__.py` hacía `from media_optimizer.cli.main import main`, y a partir de ahí
  `from media_optimizer.cli import main` devolvía **la función**, no el módulo. Apareció al
  escribir un test que necesitaba el módulo. Se quitó el reexport y el punto de entrada
  apunta a `cli.main:main`. **Vale como regla general: no reexportar un nombre que coincida
  con el de un submódulo del mismo paquete.**

- **Una regla de arquitectura que busca texto suelto confunde el uso con la copia.** La
  primera versión de la regla que prohíbe duplicar el registro marcaba el nombre del comando
  `run`, porque coincide con el del reporte `run`. Mirar **colecciones literales** —que es
  lo que "una lista copiada a mano" significa— la volvió precisa. Es el tercer caso en el
  proyecto en que un análisis de código confunde niveles: el grep de HU-010 marcó una
  palabra dentro de una docstring, el guardián de HU-160 marcó la explicación de su propia
  regla, y este marcó un nombre legítimo.

## Lecciones aprendidas

- **La decisión de arquitectura se pagó sola en la implementación.** Que las etapas sean
  datos del registro convirtió `run` y `report` en dos módulos de unas 30 líneas cada uno, y
  la ayuda de la CLI se genera sin que nadie mantenga una lista. La alternativa —un comando
  por etapa— habría empezado con seis módulos casi idénticos.

- **Quinta HU seguida en que el guardián se verifica por inyección** (HU-160, 168, 156, 169,
  162). Aquí era especialmente necesario: el test de sincronía es la **única** mitigación del
  único riesgo que ADR-005 identificó, y su valor depende por completo de que falle cuando
  debe. Con la desincronización inyectada, falla y nombra el campo huérfano.

- **La ayuda de la CLI es la primera superficie del proyecto que ve una persona no técnica**,
  y eso cambió decisiones pequeñas: la ayuda va en español, los nombres de comando en inglés,
  y ejecutar sin comando muestra la ayuda en vez de un error. Ninguna se decidió por gusto:
  el charter dice que el dueño del negocio es un usuario previsto.

## Decisiones rechazadas

- **Un comando por etapa** — ADR-005 se reabre a los 15 comandos, y el backlog ya define seis
  etapas más siete reportes.
- **Descubrir los comandos recorriendo la carpeta `commands/`** — haría que el conjunto de
  comandos dependiera del orden del filesystem, justo lo que el charter §6.1 prohíbe. El
  registro es una tupla explícita.
- **Banderas propias por etapa** (`--clahe-clip`) — sería criterio estético fuera del perfil.
- **Valores por defecto en el parser** — impediría distinguir "no lo indicó" de "lo indicó
  con el valor habitual", y sin esa distinción un archivo de configuración no puede
  aplicarse por debajo. Los defaults se resuelven en la frontera tipada.
- **Usar el rastro estructurado para hablarle a la persona** — son cosas distintas: una línea
  JSON por evento sirve para filtrar con herramientas, no para leerla mientras esperas.
