# Impacto de ADR-005 sobre el resto del proyecto

> Revisión ejecutada el 2026-08-06 tras aceptar ADR-005 (`argparse` con frontera tipada).
> Cubre las HUs afectadas, la matriz de impacto completa, los riesgos clasificados y la
> revisión cruzada de consistencia.

---

## 1. HU-155 — Configuración externalizada

**Enunciado:** *"Configuración externalizada: carga, validación y defaults (`config/`)"* · P0 · M

**¿Sigue siendo compatible con argparse? Sí.** La estrategia de configuración no depende de
la librería de parseo: `config/` carga y valida un archivo, y la CLI es uno de sus
consumidores.

**Pero la revisión encontró un conflicto concreto de precedencia, y requiere un cambio.**

### El problema

Una configuración externalizada implica una cadena de precedencia:

```
argumento de línea de comandos  >  variable de entorno  >  archivo de config  >  default
```

Si `argparse` declara `add_argument("--profile", default="hospedaje")`, entonces
`args.profile` vale `"hospedaje"` **tanto si el usuario no pasó nada como si lo pasó
explícitamente**. Se pierde la información de si el usuario decidió o no, y con ella la
posibilidad de que el archivo de configuración se aplique: el default del parser pisaría
siempre al del archivo.

### El cambio mínimo propuesto

**Un solo cambio, en dos frases:**

1. **El parser no lleva `default=`.** Todos los argumentos opcionales declaran
   `default=None`. Un `None` significa exactamente *"el usuario no lo indicó"*.
2. **Los valores por defecto viven en `config/`** y se aplican en la función de conversión
   —la frontera tipada— que ya existe en el patrón. El dataclass resultante nunca tiene
   campos `None`: la resolución ocurre justo ahí.

Esto no añade una pieza nueva: **usa la frontera tipada que el patrón ya exige**. Es su
lugar natural, porque es donde el `Namespace` se vuelve un contrato.

### Nota de honestidad

**Este conflicto no lo causa ADR-005.** Es idéntico con cualquier librería de parseo: el
problema es la ambigüedad entre "no pasado" y "pasado con el valor por defecto", no la
herramienta. La revisión lo destapó porque obligó a mirar la cadena de precedencia, no
porque la decisión lo introdujera.

**Acción:** anotar el cambio en la spec de HU-155 cuando se escriba. **No requiere reabrir
nada** — HU-155 no ha empezado.

---

## 2. HU-164 — Framework de golden tests

**Enunciado:** *"Framework de golden tests (comparación de imágenes con tolerancia + hash)"* · P0 · M

**¿Pueden los golden tests invocar la CLI sin depender de terceros? Sí, y de forma más
simple que con un framework.**

`argparse` acepta la lista de argumentos como parámetro: `parser.parse_args(argv)`. Basta con
que el entrypoint tenga la firma

```
main(argv: list[str] | None = None) -> int
```

para que un test invoque la CLI **en el mismo proceso**, sin subprocesos, sin utilidades de
prueba de terceros y sin tocar `sys.argv`. Con un framework habría hecho falta su ejecutor de
pruebas específico, que es una dependencia más en el camino.

### Dos precisiones que la spec de HU-164 debe recoger

1. **`argparse` levanta `SystemExit`** ante un argumento inválido o `--help`; no devuelve un
   código. Un test que ejercite esos caminos tiene que capturarlo (`pytest.raises(SystemExit)`)
   y leer `.code`. El camino feliz sí devuelve el `int` de `main`.
2. **Para comparar reproducibilidad entre ejecuciones hace falta un subproceso**, no una
   llamada en el mismo proceso: el defecto que HU-169 encontró —el orden de un conjunto—
   **es invisible dentro de un solo proceso**. El arnés ya existe y está probado en
   `tests/core/test_determinism.py::TestReproducibilidadEntreProcesos`; HU-164 lo reutiliza en
   vez de inventar otro.

**Acción:** recoger ambas precisiones en la spec de HU-164 cuando se escriba. Ningún cambio
de alcance.

---

## 3. HU-163 — Gates de calidad locales

**Enunciado:** *"Gates de calidad locales: pre-commit con ruff+mypy+pytest dirigido"* · P0 · S

**¿Siguen siendo válidos? Sí, sin cambios.**

**¿Hace falta un gate nuevo? No.** ADR-005 impone una mitigación —el test de sincronía entre
el parser y el dataclass— pero **es un test, y el gate de `pytest` ya lo ejecuta**. Añadir un
gate específico sería duplicar cobertura sin evidencia de que el existente falle.

| Gate previsto | ¿Sigue válido? | Qué cubre de ADR-005 |
|---------------|----------------|----------------------|
| `ruff check` | ✅ | `T20` (cero `print`) sigue siendo la regla que empuja a usar el rastro estructurado |
| `ruff format --check` | ✅ | Sin cambios |
| `mypy` estricto sobre `src/` | ✅ | **Es el gate que da valor a la frontera tipada**: sin él, el patrón no compra nada |
| `pytest` dirigido | ✅ | Ejecuta el test de sincronía parser↔dataclass y los de arquitectura |

### Observación anotada, sin acción

`pyproject.toml` limita mypy a `files = ["src"]`, así que **`tests/` no se verifica de
tipos**. Es anterior a ADR-005 y no hay evidencia objetiva de que haya causado ningún
defecto: los errores de tipo que se han encontrado estaban todos en `src/`. **No se propone
ampliarlo** — sería un gate nuevo sin evidencia, justo lo que la instrucción excluye. Se
anota por si algún día aparece un defecto que lo justifique.

---

## 4. Matriz de impacto completa

| Elemento | Impactado | Acción | Estado |
|----------|-----------|--------|--------|
| **ADR-005** | **Sí** | Reescrito: Aceptado, `argparse`, sin argumentos refutados; incluye alternativas, mediciones, riesgos, impacto futuro, decisión y consecuencias | ✅ Hecho |
| ADR-001 · 002 · 003 · 004 | No | Ninguna — ADR-005 no toca entorno, visión, catálogo ni filesystem | — |
| **HU-162** | **Sí** | Spec completa nueva + diseño detallado de la CLI. Nace **bloqueada** por la superficie de comandos | ✅ Hecho (bloqueada) |
| **HU-150** (cerrada) | **Sí** | Su spec decía "CLI Typer". Se añade nota de supersesión **sin reescribir la historia**; la conclusión de la spec no cambia | ✅ Hecho |
| **HU-155** | **Sí** | Un cambio mínimo: el parser sin `default=`, los defaults en `config/`, resueltos en la frontera tipada (§1) | 📋 Anotado; HU no iniciada |
| **HU-164** | **Sí** | Dos precisiones: `SystemExit` y reutilizar el arnés de subprocesos de HU-169 (§2) | 📋 Anotado; HU no iniciada |
| **HU-163** | **No** | Ninguna. El test que ADR-005 impone ya lo corre el gate de `pytest` (§3) | ✅ Verificado |
| **HU-017 · 037 · 064 · 078 · 110 · 184** | **Sí — bloqueadas** | Sus enunciados nombran comandos que la superficie pedida no contempla. **Requiere decisión** | 🔴 §6 |
| **HU-032** (etiquetado vía CLI) | **Sí** | Séptima HU que menciona la CLI y **no aparece en ninguna de las dos superficies**. Descubierta en esta revisión | 🔴 §6 |
| **Tests** | **Sí** | 2 reglas nuevas de arquitectura (`argparse` solo en `cli/`; `core/` no lo importa) + el test de sincronía por comando. **Ninguno se escribe hasta desbloquear** | 📋 Especificado en HU-162 |
| **Tests existentes** | **No** | Los 422 siguen verdes: no hay CLI todavía, nada que romper | ✅ Verificado |
| **Arquitectura** | **Sí** | `docs/blueprint/arquitectura.md` **no existía** pese a estar referenciado en CLAUDE.md. Creado con el diagrama de dependencias y las 5 reglas verificadas | ✅ Hecho |
| **Documentación — CLAUDE.md** | **Sí** | Tabla de stack (fila Interfaz) y tabla de módulos (fila `cli/`) | ✅ Hecho |
| **Documentación — charter** | **Sí** | §5 Alcance v1 decía "CLI Typer" | ✅ Hecho |
| **Documentación — reglas** | **Sí** | `.claude/rules/cli.md` nueva: el patrón de tipado obligatorio para toda CLI futura | ✅ Hecho |
| **Documentación — `python.md`** | **No** | Sus reglas son independientes de la librería de CLI | ✅ Verificado |
| **Backlog — HU-162** | **Sí** | Enunciado actualizado: nombra `argparse` y ADR-005 | ✅ Hecho |
| **Backlog — superficie de comandos** | **Sí** | 6 HUs con enunciado potencialmente falso + HU-032 + falta la HU de `scan` | 🔴 §6 |
| **`pyproject.toml`** | **Sí, cuando se implemente** | Añadir `[project.scripts]`. **Ninguna dependencia nueva** | 📋 En HU-162 |
| **`uv.lock`** | **No** | Sin dependencias nuevas, el lock no cambia | ✅ Verificado |
| **`src/`** | **No** | Instrucción explícita: no se escribe código | ✅ Respetado |
| **Métricas / gate-log** | **Sí** | Registrar el gate fallido de HU-162 con su motivo | 📋 Al cerrar esta revisión |

---

## 5. Riesgos de abandonar el framework de terceros

Detalle completo con evidencia en **ADR-005 §Riesgos**. Resumen por categoría:

| Categoría | Severidad | Síntesis |
|-----------|-----------|----------|
| **Funcional** | **Ninguna** | El prototipo cubre la superficie completa. Evidencia: 5 comandos funcionando |
| **Mantenibilidad** | **Media — el único riesgo real** | Parser y dataclass pueden desincronizarse sin que `mypy` lo vea, porque el `Namespace` es `Any`. Evidencia: dimensión 5 de la medición. Mitigado con test obligatorio |
| **DX** | Baja | Sin autocompletado; `help=` a mano; ayuda más sobria. Evidencia: dimensiones 10-11 y las salidas comparadas. Se asume |
| **Rendimiento** | **Invertida — es una ganancia** | −78 ms por invocación. Evidencia: dimensión 3 |
| **Compatibilidad** | Baja | `argparse` es stdlib con la política de compatibilidad de CPython; el intérprete está fijado en el lock |
| **Deuda técnica** | Baja hoy | 39 líneas para 5 comandos. Con umbral de reapertura objetivo: >15 comandos, >150 líneas de parser, o autocompletado como requisito |

---

## 6. Revisión cruzada de consistencia — **inconsistencias encontradas**

Solo las inconsistencias, como se pidió.

### 🔴 I-1 · La superficie de comandos contradice el backlog — **BLOQUEANTE**

Los 5 comandos indicados (`scan`, `ingest`, `inventory`, `process`, `report`) no coinciden
con los 6 que el backlog reparte en 6 HUs de 4 épicas. Fusiona dos comandos, convierte dos
reportes en comandos, añade uno sin HU y **deja tres HUs sin comando donde aterrizar** —
entre ellas HU-078 (`select`), que produce la galería ordenada: el entregable de negocio del
charter §2.

Tabla de correspondencias e impacto de cada opción: [`diseno_cli.md`](diseno_cli.md) §8.

**Impide implementar HU-162**, porque esta HU fija el registro de comandos.

### 🔴 I-2 · HU-032 menciona la CLI y no está en ninguna superficie

*"Etiquetado asistido de ambientes vía CLI (propone, humano confirma → sidecar HU-019)"* ·
P1. Es la **séptima** HU que asume un comando, y no aparece ni en los 5 pedidos ni en los 6
del backlog. Se descubrió al contrastar una por una. Debe entrar en la decisión de I-1.

### 🟡 I-3 · CLAUDE.md referenciaba dos documentos inexistentes

CLAUDE.md define la constitución como *"`docs/blueprint/` (charter, arquitectura, backlog,
estándares)"*. De los cuatro:

- `charter.md` ✅ · `backlog.md` ✅
- **`arquitectura`** ❌ no existía → **creado en esta revisión**
- **`estándares`** ❌ **sigue sin existir** como documento. En la práctica son
  `.claude/rules/*.md`, que es otra ruta y otro formato. **Sin resolver**: o se crea el
  documento, o CLAUDE.md deja de prometerlo y apunta a `.claude/rules/`.

### 🟡 I-4 · Menciones remanentes del framework descartado — **las dos son correctas**

Se verificó el repositorio completo. Quedan menciones solo en dos sitios, y ambas deben
quedarse:

| Ubicación | Por qué es correcta |
|-----------|---------------------|
| `docs/blueprint/adr/ADR-005-framework-cli.md` | Es el ADR comparativo: **nombrar la alternativa evaluada es requisito** de un ADR con evidencia. Lo que se eliminó fueron los *argumentos refutados*, no el nombre de la opción medida |
| `items/HU-162/insumos/cli-bench/` | Es el banco de medición: los prototipos **son** la evidencia reproducible del ADR. Borrarlos dejaría el ADR sin sustento |
| `items/HU-150/spec/spec_tecnica.md` | Nota de supersesión que documenta el cambio. Reescribir una spec cerrada falsificaría el registro histórico |

**Verificado: ninguna especificación requiere una librería de formato enriquecido, ninguna
arquitectura depende de una librería de parseo de terceros, y `core/` no importa `argparse`
—ni podría: no existe código de CLI todavía.**

### ✅ Verificado sin inconsistencias

- Los 4 ADRs previos no contradicen a ADR-005.
- `python.md` es independiente de la decisión.
- Los 422 tests siguen verdes; `uv.lock` sin cambios; `src/` intacto.
- Las restricciones que el equipo había puesto para el caso de adoptar un framework
  (capa delgada, cero lógica de negocio, salida persistida determinista) **siguen vigentes
  tal cual** — nunca dependieron de la librería, y están en `arquitectura.md` §3.
