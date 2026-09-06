# Feedback — HU-104

## Lecciones aprendidas

- **La funcionalidad más costosa de esta HU es la que el cliente no usa.** El backlog la
  titula *"crop 9:16 de **material horizontal**"*, y al validar apareció que el celular del
  cliente **ya graba en 9:16 nativo**: ninguno de sus clips recorta ancho, el encuadre solo
  escala. El recorte de material apaisado está implementado y probado, pero con clips
  sintéticos — no con el material real de nadie.
  **No es un error haberlo hecho** (el backlog lo pide, y otras verticales sí graban en
  horizontal), pero sí un dato para no invertir en encuadre inteligente todavía: el problema
  que resolvería no aparece en este lote.

- **Separar construir el comando de ejecutarlo puso 12 de 23 tests en milisegundos.** Los
  errores de encuadre son errores de aritmética que acaban en una cadena de texto; verificar
  esa cadena contra valores literales los detecta sin renderizar nada. Es el mismo patrón que
  el ejecutor de video ya usaba con su validación silenciosa, y vuelve a pagar.

- **Acotar es mejor que fallar cuando el resultado acotado sigue siendo correcto.** Un
  desplazamiento excesivo podía tratarse como error de programación —levantar excepción— o
  como intención mal expresada. Se eligió lo segundo porque el encuadre acotado es
  perfectamente válido, y fallar convertiría un parámetro mal puesto en un lote interrumpido
  a la mitad. **El criterio no es "ser permisivo", es si lo que queda al acotar sigue
  cumpliendo el contrato.** Aquí sí; en `SceneThresholds` de HU-103, un umbral fuera de rango
  no cumple nada y por eso ahí sí se falla.

- **Devolver el encuadre en vez de un booleano.** `crop_to_vertical` devuelve qué se aplicó,
  no si funcionó. HU-110 tendrá que explicar al usuario qué parte de su material se recortó,
  y esa información solo existe en el momento del recorte.

## Decisiones rechazadas

- **Encuadre inteligente (detectar el sujeto y recortar alrededor)** — no tiene HU en el
  backlog y exigiría detección de contenido. El enunciado pide *centrado configurable*, que
  es lo que se entregó.
- **Fallar ante un desplazamiento excesivo** — ver arriba.
- **Rehacer la aritmética del encuadre** — ya existía desde la tanda de HU-135, probada con
  valores literales para 4K, 1080p, 4:3 y vertical. Esta HU solo la aplica.
- **Afinar codec, bitrate y perfil de color** — es HU-109. La salida de aquí es correcta pero
  no está optimizada para plataforma.

## Anotado

`read_dimensions` abre el clip con la librería de visión para leer solo la cabecera. Cuando
HU-100 (ingesta de clips con streaming) llegue, conviene revisar si esa lectura debe pasar
por ella en vez de hacerse aquí — es el mismo punto que HU-102 dejó anotado sobre el muestreo
de cuadros.
