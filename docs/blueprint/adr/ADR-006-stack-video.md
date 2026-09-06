# ADR-006 — Stack de video: ffmpeg por subprocess + PySceneDetect

- **Estado:** **Propuesto** — no puede aceptarse todavía; ver «Qué falta para pasar a Aceptado»
- **Fecha:** 2026-09-05
- **Origen:** HU-154 (backlog E7) · habilita HU-003, HU-014, HU-100–112, HU-167
- **Decisores:** equipo técnico (@oscardacto) · análisis: Claude (orquestador-ejecutor ASDD)

---

## Contexto

El backlog reserva la épica E5 (13 HUs) para video: detección de escenas, score por escena,
crop 9:16, secuenciado narrativo, ensamblado y export. Nada de eso puede empezar sin decidir
cómo se invoca el procesamiento de video.

HU-154 impone una condición explícita:

> *"**Obligatorio: validar la cadena contra la matriz de compatibilidad de rutas de ADR-004
> antes de adoptarla**."*

Esa condición es la que mantiene este ADR en «Propuesto».

## Alternativas evaluadas

| | Alternativa | Evaluación |
|---|---|---|
| **A** | `subprocess` de la stdlib invocando el binario `ffmpeg` | **0 dependencias Python.** El grafo de filtros se construye como lista de argumentos. Control total sobre los flags de determinismo |
| **B** | `ffmpeg-python` | Envuelve exactamente lo mismo —construye una lista de argumentos y llama a `subprocess`— añadiendo una dependencia y una capa de traducción. No aporta seguridad de tipos sobre el grafo: sus nodos son `Any` |
| **C** | `PyAV` (bindings de libav) | Da control por frame y evita el proceso externo, pero es una extensión compilada pesada, y para concatenar/transicionar clips reimplementaríamos lo que `filter_complex` ya hace |

**PySceneDetect** no compite con las anteriores: resuelve la detección de escenas (HU-101),
que es un problema distinto del ensamblado. Se adopta por separado y **con su propia
instalación cuando HU-101 entre a DEV**, no ahora.

## Decisión propuesta

**Alternativa A: `subprocess` con lista de argumentos, sin dependencia Python nueva para
invocar ffmpeg.** Mismo criterio con el que ADR-005 eligió `argparse`: la alternativa de
terceros envuelve lo mismo que hace la stdlib y su coste es permanente.

`shell=False` siempre — la lista de argumentos nunca pasa por un intérprete de comandos, así
que un nombre de archivo con caracteres especiales no puede convertirse en una inyección.
Esto satisface la prohibición de `subprocess(..., shell=True)` de las reglas del proyecto
sin necesitar excepción.

## Política de determinismo (obligatoria)

El charter promete que la misma entrada produce la misma salida. En video eso no sale gratis:

| # | Regla | Por qué |
|---|-------|---------|
| **D-1** | `-filter_complex_threads 1` en toda invocación con `filter_complex` | El reparto del grafo entre hilos altera el orden de evaluación de las funciones de estado del evaluador de expresiones. Con más de un hilo, dos corridas del mismo grafo pueden diferir |
| **D-2** | `setpts=PTS-STARTPTS` inmediatamente después de cada corte de vídeo, y `asetpts=PTS-STARTPTS` en el de audio | Un segmento recortado conserva las marcas de tiempo de su origen. Sin reiniciarlas a cero, la concatenación produce marcas no monótonas: frames descartados y desfase A/V |
| **D-3** | `-nostdin` | Sin él, ffmpeg puede quedarse esperando entrada del teclado y colgar un lote desatendido |
| **D-4** | `-map_metadata -1` en toda salida | La salida nace sin metadatos del original: ni GPS ni datos personales. Misma garantía que el export de fotos |
| **D-5** | Sin `-map 0` implícito ni comodines de entrada; toda entrada se declara con su índice | El orden de los streams no puede depender de cómo el contenedor los ordenó |

Estas reglas viven en el ejecutor, no en quien lo llama: **no se pueden olvidar porque el
llamador no las escribe**.

## Dominio sin IO

`core/` y `ranking/` no importan este módulo, no conocen la ruta del binario ni construyen
argumentos. El test de arquitectura ya prohíbe que el dominio importe infraestructura, y esta
decisión añade dos reglas verificadas:

- Ningún módulo fuera de la capa de video invoca `subprocess`.
- El dominio no importa `media_optimizer.video`.

## Acceso al filesystem

ffmpeg **recibe rutas y las abre por su cuenta** — el mismo patrón que en HU-156 se midió
destructivo en el manejador de archivos de la biblioteca estándar, que descartaba registros
en silencio ante un nombre de dispositivo.

Por eso toda ruta entregada a ffmpeg pasa por la capa de adaptación de ADR-004 antes de
entrar en la lista de argumentos. **Que ffmpeg acepte la forma extendida de Windows no está
verificado**: el binario no está instalado en la máquina de referencia, y suponerlo sería
exactamente el error que ADR-004 nació para evitar.

## Consecuencias

**Positivas**
- El proyecto sigue con dos dependencias Python de producción. La única incorporación es un
  binario externo, sustituible y sin superficie de importación.
- Las cinco reglas de determinismo son inevitables por construcción.
- El grafo de filtros se puede validar en milisegundos sin renderizar (ver el ejecutor), así
  que un error de sintaxis se detecta antes de gastar minutos de cómputo.

**Negativas / mitigación**
- Depender de un binario externo con versión propia → se registra la versión detectada en el
  rastro de cada ejecución, para que un cambio de comportamiento sea rastreable.
- El grafo de filtros es texto, y el verificador de tipos no lo entiende → se compensa con la
  validación silenciosa contra el binario real.

## Qué falta para pasar a Aceptado

1. **Instalar ffmpeg en la máquina de referencia.** Hoy no está: `ffmpeg -version` no responde.
2. **Validar la cadena contra la matriz de rutas de ADR-004** — la condición que HU-154 exige
   literalmente. Concretamente: comprobar si ffmpeg lee y escribe con la forma extendida de
   Windows, con nombres largos y con nombres que coinciden con dispositivos del sistema.
   El test condicional de esta HU ejecuta esa comprobación en cuanto el binario exista.
3. Aprobación del equipo para incorporar el binario y, cuando llegue HU-101, `PySceneDetect`.

**Mientras 1 y 2 no se cumplan, ninguna HU de E5 puede cerrarse**: se estaría construyendo
sobre una suposición de compatibilidad de rutas que el propio backlog prohíbe asumir.
