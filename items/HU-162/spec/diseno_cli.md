# Diseño de la CLI — media-optimizer

> Diseño completo previo a la implementación. Fijado por **ADR-005** (`argparse`) y por la
> regla `.claude/rules/cli.md`. **Ninguna línea de código escrita todavía.**

---

## 1. Estructura de archivos

```
src/media_optimizer/cli/
├── __init__.py          exporta main
├── main.py              entrypoint: parser raíz, despacho, traducción de errores
├── exit_codes.py        el enumerado ExitCode
├── errors.py            traducción de excepciones del dominio → mensaje + código
└── commands/
    ├── __init__.py      registro de comandos (lista explícita, sin descubrimiento dinámico)
    ├── scan.py          ── cada módulo aporta las 4 piezas del patrón:
    ├── ingest.py           1) dataclass congelado de argumentos
    ├── inventory.py        2) registro de su subparser
    ├── process.py          3) conversión Namespace → dataclass
    └── report.py           4) ejecución, que invoca al dominio
```

**Sin descubrimiento dinámico de comandos.** El registro es una tupla explícita: un
comando existe porque está escrito en una lista, no porque un módulo apareció en una
carpeta. Importar por nombre de archivo haría que el conjunto de comandos dependiera del
orden del filesystem, que es justo lo que el charter §6.1 prohíbe.

### Por qué un módulo por comando

Cada comando lleva sus cuatro piezas juntas. Un archivo único con los cinco crecería a más
de 300 líneas —el límite de `python.md`— antes del tercer comando, y mezclaría cinco
contratos de entrada sin relación entre sí.

---

## 2. Comandos

| Comando | Qué hace | Lee | Escribe | HU que lo implementa |
|---------|----------|-----|---------|----------------------|
| `scan` | Recorre una carpeta y reporta **qué hay**, sin producir nada | carpeta de origen | solo consola | ⚠️ sin HU asignada — ver §8 |
| `ingest` | Carpeta → catálogo validado + cuarentena de lo ilegible | carpeta de origen | catálogo JSON en el workspace | HU-017 |
| `inventory` | Catálogo → tabla por asset (dimensiones, orientación, flags) | catálogo | reporte en `reports/` | HU-018 |
| `process` | Catálogo → análisis y revelado según el perfil | catálogo + perfil | derivados en el workspace | ⚠️ agrupa HU-037/064 — ver §8 |
| `report` | Estado del run → reporte consolidado legible | workspace | reporte en `reports/` | HU-181 |

### Diferencia entre `scan` e `ingest` — no son lo mismo

`scan` es de **solo lectura**: no crea el workspace, no escribe catálogo, no aparta nada.
Responde *"¿qué tengo en esta carpeta y qué va a pasar con ello?"* antes de tocar nada.
`ingest` sí produce estado.

Esa separación tiene una justificación medida: en el lote real del cliente, **72 de 82 fotos
salieron marcadas por un defecto de interpretación de EXIF** (HU-004) y **15 grupos de
archivos resultaron ser el mismo contenido con nombres distintos** (HU-013). Un comando que
deja mirar antes de escribir convierte esos hallazgos en algo que el usuario ve antes de
generar nada, no después.

---

## 3. Argumentos

### Globales — antes del comando

| Argumento | Tipo | Por defecto | Para qué |
|-----------|------|-------------|----------|
| `--version` | flag | — | Versión y sale |
| `--workspace RUTA` | ruta | `./salidas` | Directorio de trabajo (HU-016) |
| `--profile NOMBRE` | texto | `hospedaje` | Perfil de negocio (HU-160) |
| `--log-level NIVEL` | enumerado | `INFO` | `DEBUG` · `INFO` · `WARNING` · `ERROR` (HU-156) |
| `--log-file RUTA` | ruta | ninguno | Además de la consola, deja el rastro en un archivo |
| `--quiet` | flag | falso | Solo errores por consola |

`--workspace` y `--profile` son globales, no por comando: son el **contexto del run**, no un
parámetro de una etapa. Repetirlos en cada subcomando obligaría al usuario a escribirlos dos
veces al encadenar comandos.

### Por comando

| Comando | Posicional | Opciones propias |
|---------|-----------|------------------|
| `scan` | `origen` (carpeta) | `--recursive/--no-recursive` (por defecto sí) |
| `ingest` | `origen` (carpeta) | `--recursive/--no-recursive`, `--force` (re-ingerir aunque exista catálogo) |
| `inventory` | — (usa el catálogo del workspace) | `--format {texto,markdown}` |
| `process` | — | `--stage {analyze,develop,all}` (por defecto `all`) |
| `report` | — | `--format {texto,markdown}` |

### Contrato de entrada de cada comando

```
ScanArgs      (source: Path, recursive: bool)
IngestArgs    (source: Path, recursive: bool, force: bool)
InventoryArgs (output_format: OutputFormatName)
ProcessArgs   (stage: StageSelection)
ReportArgs    (output_format: OutputFormatName)

RunContext    (workspace: Path, profile: str, log_level: str,
               log_file: Path | None, quiet: bool)
```

Cada uno es un **dataclass congelado con `slots=True`**. El `RunContext` lleva lo global y se
construye una sola vez. Ninguno menciona `argparse`.

---

## 4. Ayuda

- `media-optimizer --help` → propósito, opciones globales, lista de comandos con una línea
  cada uno.
- `media-optimizer <comando> --help` → argumentos del comando, con `help=` **escrito a mano**
  para cada opción (ADR-005 lo contabilizó como coste asumido).
- Ejecutar sin comando → **la ayuda y código de salida 2**, no un error críptico.

**Toda la ayuda en español**, como el resto de la documentación de cara al usuario. Los
nombres de comandos y opciones van en inglés, como el código.

---

## 5. Códigos de salida

```python
class ExitCode(IntEnum):
    OK = 0                  # todo bien
    FAILURE = 1             # el run falló: nada utilizable
    USAGE = 2               # argumentos mal escritos (lo impone argparse)
    INVALID_INPUT = 3       # entrada legible pero inservible: perfil roto, carpeta vacía
    PARTIAL = 4             # terminó, pero hubo assets apartados o etapas degradadas
```

**`2` está reservado por `argparse`** para errores de uso y no puede significar otra cosa.

**`PARTIAL = 4` es la razón de ser de este enumerado.** El charter exige que un archivo
corrupto degrade ese asset y no tumbe el lote — es decir, **el caso normal es terminar con
fallos parciales**. Con solo `0` y `1` habría que elegir entre mentir (0, ocultando que 12
fotos quedaron en cuarentena) o alarmar (1, cuando el resultado sirve). Un script que
encadene comandos necesita distinguirlo, y ese es exactamente el escenario de HU-184.

| Código | Cuándo | Qué ve el usuario |
|--------|--------|-------------------|
| `0` | Todos los assets procesados | Resumen |
| `1` | El run no pudo completarse | Causa y qué hacer |
| `2` | Argumento inválido o comando ausente | Ayuda |
| `3` | Perfil inexistente/corrupto, carpeta sin medios | Qué corregir |
| `4` | Terminó con assets en cuarentena o etapas degradadas | Resumen + cuántos y por qué |

---

## 6. Errores

Traducción directa de la jerarquía de HU-161, que ya existe:

| Excepción | Código | Qué se muestra |
|-----------|--------|----------------|
| `InvalidInputError` | `3` | El mensaje del error, que ya está redactado para el usuario |
| `CorruptMediaError` | `4` si el lote siguió · `1` si era el único asset | Ruta y causa; el asset va a cuarentena |
| `MediaOptimizerError` (base) | `1` | Mensaje del error |
| Cualquier otra excepción | **se propaga con su traza completa** | Traza — es un bug, no un fallo esperable |

**Un bug no se disfraza de error del dominio.** El docstring de `core/errors.py` ya lo fija:
*"envolver un bug en un error del dominio lo escondería en el resumen de fallos del lote"*.
La CLI hereda esa regla: solo captura `MediaOptimizerError`.

**Ningún fallo esperable muestra un stacktrace.** Un perfil mal escrito produce una frase que
dice qué corregir, no cincuenta líneas de traza.

---

## 7. Contratos con el resto del sistema

Lo que la CLI puede invocar, y lo único:

```
cli/  ──▶  pipeline/     orquestación de etapas
      ──▶  workspace     Workspace(root).ensure()
      ──▶  logs          configure_logging(level, stream, log_file)
      ──▶  profiles/     carga del BusinessProfile
      ──▶  core/         los contratos, como tipos de datos
```

**La CLI nunca invoca `ingest/`, `photo/`, `video/` ni `vision/` directamente** — eso es
trabajo de `pipeline/`. Si un comando necesitara llamar a una etapa concreta, la orquestación
está en el lugar equivocado.

---

## 8. ⚠️ Bloqueo detectado: la superficie de comandos no coincide con el backlog

**No se puede implementar hasta resolverlo.** No es una preferencia de nombres: cambia qué HU
implementa qué.

### La divergencia, medida

| Comando pedido | HU del backlog que le correspondería | Estado |
|----------------|--------------------------------------|--------|
| `scan` | **ninguna** | ❌ No existe HU para un comando de solo lectura |
| `ingest` | HU-017 `CLI ingest: carpeta → catálogo + resumen` | ✅ Coincide |
| `inventory` | HU-018 `Reporte de inventario del lote` | ⚠️ En el backlog es un **reporte**, no un comando |
| `process` | HU-037 `CLI analyze` **+** HU-064 `CLI develop` | ⚠️ **Fusiona dos comandos del backlog en uno** |
| `report` | HU-181 `Reporte consolidado del run` | ⚠️ En el backlog es un **reporte**, no un comando |
| — | HU-078 `CLI select` | ❌ **Queda sin comando asignado** |
| — | HU-110 `CLI reel` | ❌ **Queda sin comando asignado** |
| — | HU-184 `CLI run` (pipeline completo) | ❌ **Queda sin comando asignado** |

El backlog define **6 comandos** (`ingest`, `analyze`, `develop`, `select`, `reel`, `run`)
repartidos en 6 HUs de 4 épicas. La superficie pedida son **5 comandos** con fronteras
distintas: fusiona dos, convierte dos reportes en comandos, añade uno nuevo y deja tres HUs
sin comando donde aterrizar.

### Impacto si se implementa sin resolverlo

- **6 HUs quedan con enunciado falso** (HU-017, HU-037, HU-064, HU-078, HU-110, HU-184). Su
  criterio de aceptación menciona un comando que no existiría.
- **HU-078 (`select`) es P1 y HU-184 (`run`) es P1**: sin comando asignado, la selección y el
  pipeline completo dejan de ser alcanzables desde la CLI. `select` es el que produce la
  galería ordenada — el entregable de negocio del charter §2.
- **`process --stage all` fusiona análisis y revelado**, que en el backlog son etapas
  separadas con presupuestos de rendimiento distintos (HU-165). Un solo comando con un solo
  `StageReport` perdería la granularidad que HU-168 acaba de establecer.
- **`scan` no tiene HU**, así que no tiene criterios de aceptación ni entra en ninguna épica.

### Las dos salidas posibles

**Opción 1 — la superficie pedida es la buena.** Entonces hay que actualizar el backlog:
reescribir el enunciado de las 6 HUs, crear la HU de `scan`, y decidir dónde aterrizan
`select`, `reel` y `run`. Es trabajo de backlog, no de código, y **debe hacerse antes** de
que HU-162 fije el registro de comandos.

**Opción 2 — el backlog es el bueno** y los 5 nombres eran una descripción aproximada.
Entonces la CLI expone `ingest`, `analyze`, `develop`, `select`, `reel`, `run`, y `scan`,
`inventory` y `report` se resuelven como opciones de los existentes (`ingest --dry-run`,
`inventory` como salida de HU-018, `report` como salida de HU-181).

**No la resuelvo por mi cuenta**: la primera cambia 6 HUs de 4 épicas y la segunda contradice
una instrucción explícita. Cualquiera de las dos es implementable de inmediato una vez
decidida; lo que no es defendible es escribir el registro de comandos sin saber cuál rige.

---

## 9. Qué queda listo para implementar en cuanto se resuelva §8

Todo lo demás de este documento es independiente de la decisión: la estructura de archivos,
el patrón de cuatro piezas, los argumentos globales, los códigos de salida, la traducción de
errores y los contratos con el resto del sistema **no cambian** con ninguna de las dos
opciones. Solo cambia la lista de módulos dentro de `commands/`.
