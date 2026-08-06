# Feedback — HU-156

## Anti-patrones detectados

- **El fallo que no lanza excepción es el que hay que buscar.** `logging.FileHandler` con un
  archivo llamado `NUL.log` devuelve un handler perfectamente funcional que escribe al
  dispositivo nulo: cero errores, cero registros. Una prueba de "¿lanzó error?" habría dado
  verde. **Regla que sale de aquí: cuando lo que se prueba es que algo quedó escrito, la
  aserción se hace sobre los bytes en disco, no sobre la ausencia de excepción.**

- **La regla de arquitectura tenía un hueco de forma, no de contenido.** Vigilaba `open`,
  `os.*` y los métodos de `Path` — todo lo que *dice* que toca disco. No veía una clase de
  terceros que lo hace por dentro. Cualquier dependencia futura que reciba una ruta y la
  abra sola (un lector de video, un serializador) entra por el mismo hueco. La regla ahora
  lista abridores conocidos, pero **el patrón a vigilar es "recibe una ruta y la abre por
  dentro", no una lista cerrada de nombres**.

## Lecciones aprendidas

- **Un defecto medido en una HU reaparece en otra capa.** `os.path.abspath` destruye nombres
  de dispositivo: se midió en HU-010 sobre nuestro propio código, y aquí volvió dentro de la
  biblioteca estándar. Que ADR-004 exija una capa única no basta si las dependencias traen
  su propia normalización escondida. **Toda dependencia que reciba rutas hay que medirla
  contra la matriz de casos hostiles antes de adoptarla** — es exactamente lo que el backlog
  ya exige para el stack de video en HU-154, y ahora hay precedente de que no es paranoia.

- **Tercera HU seguida en que el guardián se verifica por inyección** (HU-160, HU-168,
  HU-156). Ya no es una precaución puntual: es como se cierra una prueba de gobernanza en
  este proyecto. En las tres, la prueba pasaba a la primera; en dos de ellas la versión
  inicial tenía un defecto real que solo la inyección reveló.

## Decisiones rechazadas
- **Usar `logging.FileHandler` tal cual** — medido que pierde registros en silencio.
- **Prohibir heredar de `FileHandler`** — envolverlo es precisamente la forma correcta de
  adaptarlo; la regla distingue la llamada de la herencia, y hay test de ambas.
- **Rotación de logs** — sin HU asignada y sin consumidor; hereda el mismo defecto de
  `abspath` y tendría el mismo arreglo cuando llegue.
- **Que el log fuera una salida comparable en golden tests** — lleva marca de tiempo. Misma
  conclusión que HU-168: no se disfraza de determinista.

## Cambio de configuración registrado
`pyproject.toml` excluye `items/` de ruff: los scripts de medición que viven ahí **tienen**
que usar IO directo y `print` — es lo que miden. Antes de excluirlo, ruff marcaba 6 errores
en un archivo que es evidencia, no librería.
