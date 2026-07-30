# ADR-004 — Identidad de un asset, acceso al filesystem y contrato de resiliencia

- **Estado:** Propuesto — se ratifica como *Aceptado* al integrar `feature/HU-010-nombres-hostiles`
- **Fecha:** 2026-07-26
- **Origen:** HU-010 · evidencia en `items/HU-010/insumos/evidencia-empirica.md`
- **Decisores:** equipo técnico (@oscardacto) · análisis: Claude (orquestador-ejecutor ASDD)

> **Alcance deliberadamente estrecho.** Este ADR registra únicamente decisiones caras de
> revertir: qué identifica a un asset, cómo se accede al disco y qué invariantes no pueden
> romperse. El diseño de módulos, los contratos internos y la estrategia de pruebas viven
> en `items/HU-010/spec/spec_tecnica.md` — una sola fuente de verdad por tipo de decisión.

---

## Contexto

Al ejecutar la ingesta sobre datos reales aparecieron comportamientos del sistema de
archivos que ninguna prueba sintética había provocado. La evidencia completa y reproducible
está en el insumo citado; lo relevante para decidir:

1. Un archivo llamado `CON.jpg` **bloquea el proceso indefinidamente** al abrirlo por ruta
   normal. No lanza excepción: se cuelga. Ninguna cuarentena lo salva, porque el bloqueo
   ocurre antes de que exista un error que capturar.
2. Archivos con punto o espacio final, nombres de dispositivo y rutas de más de 260
   caracteres **aparecen en el listado pero fallan al abrirse**, o —peor— devuelven
   `None`/0 bytes sin excepción.
3. Rutas de más de 260 caracteres **se omiten del escaneo en silencio**.
4. **Con prefijo de ruta extendida (`\\?\`), las 70 combinaciones probadas del stack
   funcionan: cero fallos.** Con ruta normal fallan 41 de 70. La mejora es transparente:
   los archivos corrientes se comportan igual con y sin prefijo.

La conclusión que ordena todo lo demás: **el problema no son los nombres, es la forma en
que nos dirigimos al sistema de archivos.** Una solución basada en listas negras de nombres
reservados habría descartado material legítimo del usuario y habría dejado la lógica
repartida por cada módulo que toca disco.

---

## Decisión 1 — La identidad de un asset es su contenido

**El identificador de un asset es el hash de su contenido. El nombre y la ruta son
metadatos, nunca identidad.**

Consecuencias que esto fija:

- Dos archivos con el mismo contenido y distinto nombre son **el mismo asset** (ya lo
  implementa HU-006).
- El mismo archivo movido de carpeta sigue siendo el mismo asset — de ahí que el catálogo
  guarde rutas **relativas** a la raíz del lote (HU-012).
- Un nombre inaccesible **no invalida al asset**: si su contenido puede leerse, el asset
  existe y entra al pipeline.
- La re-ingesta idempotente (HU-013) compara por contenido, no por ruta.

Esta decisión es la que hace posible la Decisión 2: si la identidad dependiera del nombre,
un nombre problemático obligaría a descartar el asset.

---

## Decisión 2 — Todo acceso a disco pasa por una única capa de adaptación

**Ningún módulo del sistema construye, normaliza ni interpreta rutas del sistema operativo
por su cuenta. Todo acceso físico se hace a través de una capa de adaptación del filesystem
que traduce la ruta a la forma que la plataforma requiere.**

- En Windows, esa capa aplica el prefijo de ruta extendida sobre una ruta absoluta ya
  resuelta.
- En POSIX, la capa es la identidad — no hay bifurcación de comportamiento en el código de
  dominio.
- **El resto del sistema nunca conoce `\\?\`.** No aparece en el catálogo, ni en los
  reportes al usuario, ni en comparaciones, ni en los tests de otros módulos.

Queda **prohibido** por esta decisión:

- listas negras de nombres reservados,
- ramas `if` por plataforma fuera de la capa de adaptación,
- descartar un archivo por cómo se llama,
- que cualquier módulo de `src/` use `open()`, `Path.read_bytes/write_bytes/read_text/
  write_text/stat/exists/iterdir/glob/walk`, `os.*`, `shutil.*` o `cv2.imread/imwrite`
  sobre rutas sin pasar por la capa,
- incorporar una dependencia que acceda a disco sin integrarla a través de la capa.

**Única excepción:** los archivos de `tests/` pueden usar IO directo para *sembrar*
fixtures — crear un caso hostil exige precisamente saltarse la normalización que la capa
aplica. Lo que esos tests ejercitan debe seguir pasando por la capa.

La forma prefijada es un **detalle de transporte**, no un dato: se aplica al cruzar hacia el
disco y no sobrevive al regreso.

---

## Decisión 3 — Qué significa que el pipeline sea *fail-safe*

**Invariante fundamental: ningún archivo individual puede bloquear, detener ni corromper la
ejecución completa del pipeline.**

Se descompone en cuatro garantías que ningún WorkItem puede romper:

| # | Invariante | Qué prohíbe |
|---|---|---|
| I-1 | **Sin bloqueo indefinido.** Ninguna entrada del usuario puede dejar el proceso sin retorno | Abrir rutas sin adaptar |
| I-2 | **Sin pérdida silenciosa.** Todo archivo presente en la carpeta de entrada termina *o* procesado *o* registrado con causa | Omitir entradas sin dejar constancia |
| I-3 | **Sin corrupción del origen.** Ninguna operación modifica los archivos del usuario | Escribir, mover o renombrar en la carpeta de origen |
| I-4 | **Degradar, no abortar.** El fallo de un asset no interrumpe el lote | Propagar excepciones por asset hasta la orquestación |

I-2 es el que la evidencia mostró roto hoy: las rutas largas desaparecían sin aviso.

---

## Decisión 4 — Cuándo un archivo entra y cuándo va obligatoriamente a cuarentena

Regla de decisión, en este orden:

1. **Si su contenido puede leerse a través de la capa de adaptación, el archivo entra** —
   sin importar cómo se llame. El nombre no es criterio de exclusión.
2. **Va a cuarentena solo si, ya adaptada la ruta, sigue sin poder procesarse**, y siempre
   con causa registrada: ilegible, vacío, formato desconocido, formato no soportado,
   truncado o desproporcionado (las causas que HU-009 y HU-011 ya definieron).
3. **Ningún archivo se omite en silencio jamás.** Si no entra, está en cuarentena con
   causa. No existe una tercera categoría.

Corolario para las salidas: al **escribir** en el directorio de trabajo (HU-016), el nombre
sí se normaliza, porque la ruta extendida permite crear nombres que después son inaccesibles
por vías normales. Adaptar la ruta y sanear el nombre son problemas distintos: el primero es
de lectura, el segundo de escritura.

---

## Consecuencias

**Positivas**
- Desaparece la clase entera de fallos por nombre: no hay que enumerar casos hostiles,
  porque no se tratan caso por caso.
- El invariante I-1 pasa de aspiración a propiedad verificable con un test que hoy falla.
- La lógica específica de plataforma queda confinada a un punto auditable.
- Coste nulo en el caso normal (verificado: 14/14 operaciones idénticas con y sin prefijo).

**Negativas / mitigación**
- Un módulo que olvide usar la capa reintroduce el problema en silencio → la spec de HU-010
  define cómo se detecta esto en pruebas; los módulos de `ingest/` ya existentes se migran
  en esa misma HU.
- La ruta prefijada podría filtrarse a un dato persistido o a un mensaje al usuario → el
  catálogo guarda rutas relativas (HU-012) y los reportes muestran rutas presentables.

**Deuda declarada**
- `ffmpeg` y `PySceneDetect` **no se pudieron verificar** (no están instalados; instalarlos
  sin ADR violaría la regla del proyecto). **HU-154 queda obligada a validar la cadena de
  video contra la misma matriz antes de adoptarla**, y si alguna pieza no tolera rutas
  extendidas, a documentar en un ADR sucesor dónde termina esta abstracción.
- Verificado sobre NTFS en una sola máquina. FAT32, exFAT, unidades de red y WSL quedan sin
  probar.

---

## Cuándo reconsiderar

1. Si aparece una dependencia del stack incompatible con rutas extendidas (candidato
   principal: la cadena de video).
2. Si el proyecto pasa a soportar sistemas de archivos donde el prefijo no aplique o se
   comporte distinto.
3. Si alguna vez se necesitara que la identidad del asset dependa del nombre — lo que
   invalidaría la Decisión 1 y, con ella, la 4.
