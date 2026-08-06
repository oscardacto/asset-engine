# ADR-005 — Framework de la CLI: `argparse` de la biblioteca estándar

- **Estado:** **Aceptado** — 2026-08-06
- **Origen:** HU-162 (backlog E7) · habilita HU-017, HU-037, HU-064, HU-078, HU-110, HU-184
- **Decisores:** equipo técnico (@oscardacto) · medición y análisis: Claude (orquestador-ejecutor ASDD)
- **Reemplaza:** las dos versiones previas de este ADR, que argumentaban sin haber medido.
  Todo lo que sigue está sostenido por mediciones reproducibles; los argumentos que la
  medición refutó **no se conservan**, ni siquiera como historia — están en el registro de
  git si alguna vez hicieran falta.

---

## Contexto

El charter §2 define el producto como una CLI local. La tabla de stack proponía Typer con
la salvedad de que *"cada fila se confirma con su ADR antes de escribir código que dependa
de ella"*. HU-162 es ese código.

### Criterio de decisión (fijado por el equipo, 2026-08-06)

> **Minimizar la complejidad permanente.** Una dependencia solo se incorpora si aporta un
> beneficio **estructural** superior al coste de mantenerla durante toda la vida del
> proyecto. No se optimiza la velocidad de escribir código, sino la mantenibilidad del
> sistema dentro de dos años.

### Superficie a cubrir

5 comandos, cada uno con un argumento posicional de ruta y 2–3 opciones de tipos simples
(ruta, texto, enumerado). Sin subcomandos anidados, sin parsing dinámico, sin flags
mutuamente excluyentes.

---

## Alternativas evaluadas

| | Alternativa | Descripción |
|---|---|---|
| **A** | `argparse` leyendo del `Namespace` | Uso idiomático directo: el resultado del parseo se consume tal cual |
| **B** | `argparse` + frontera tipada | El `Namespace` se convierte de inmediato en un dataclass congelado, que es lo único que el resto del sistema ve |
| **C** | `Typer` | Framework de terceros que deriva la CLI de las anotaciones de tipo |

`click` se descartó sin medirlo en profundidad por un hecho comprobado: en la versión actual
de Typer **ya no aparece en su árbol de dependencias**, así que dejó de ser la opción de
menor huella que fue históricamente; frente a `argparse` paga una dependencia sin aportar la
verificación de tipos que sí da B.

---

## Resultados medidos

Tres prototipos **funcionalmente equivalentes** de la CLI real, medidos en la máquina de
referencia (Windows 10 Pro 19045, Python 3.13.2). El entorno con la dependencia de terceros
se creó **aislado y desechable**; no se agregó nada a `pyproject.toml`. Prototipos, variantes
con error deliberado y salidas capturadas: `items/HU-162/insumos/cli-bench/`.

| # | Dimensión | A · `argparse` | B · `argparse` tipado | C · `Typer` |
|---|-----------|----------------|------------------------|-------------|
| 1 | Dependencias transitivas | **0** | **0** | **7** |
| 2 | Huella en disco | 0 KB | 0 KB | **7 512 KB** — 5 077 de ellos un resaltador de sintaxis que esta CLI nunca usa |
| 3 | Arranque, mediana de 5 procesos | **44,6 ms** | **44,6 ms** | **122,3 ms** (2,7×) |
| 4 | Líneas de código propio (5 comandos) | 23 | **39** | 34 |
| 5 | **`mypy --strict` detecta un error de tipo sobre el argumento parseado** | ❌ **No** — reporta *"Success: no issues found"* con el error presente | ✅ **Sí** | ✅ **Sí** |
| 6 | Líneas acopladas a la librería | 2 | **2** | **9** |
| 7 | Firmas de función que mencionan la librería | 1 | **1** (recibe un dataclass propio) | **5** — una por comando |
| 8 | Crecimiento del acoplamiento | constante | **constante** | **lineal**: +1 decorador y +1 firma por comando nuevo |
| 9 | Coste de migrar a otra librería | 2 funciones | **2 funciones** | 5 firmas + 5 decoradores, creciendo |
| 10 | Autocompletado de shell | no | no | **sí** |
| 11 | Ayuda derivada del docstring | no | no | **sí** |

**Comandos exactos para reproducirlo** — ver anexo.

### Lo que la medición refutó

Dos argumentos que se habían dado por buenos **son falsos** y por eso no aparecen en este
ADR como razones:

1. *"argparse renuncia al tipado."* Falso. La renuncia es de la variante A, no de argparse.
   La variante B recupera la verificación completa de `mypy --strict` por **5 líneas más que
   Typer** (39 vs 34).
2. *"Una librería de formato enriquecido amenaza el determinismo porque adapta la salida al
   ancho del terminal."* Falso como criterio de decisión: **la ayuda de `argparse` también
   cambia con el ancho** (341 → 279 bytes entre 60 y 120 columnas; la de Typer, 856 → 1 575).
   Ninguna de las dos escribe la salida persistida del pipeline, que la genera código propio.
   El determinismo **no distingue entre las alternativas** y no puede usarse para elegir.

---

## Decisión final

**Se adopta la alternativa B: `argparse` de la biblioteca estándar, con frontera tipada
explícita.**

El parser se construye con `argparse`; su `Namespace` se convierte de inmediato en un
dataclass congelado que es lo único que el resto del sistema ve. El patrón exacto es
obligatorio y está normado en `.claude/rules/cli.md`.

**Razón dominante:** una vez que la medición empata el tipado (dimensión 5), el único
diferencial que le quedaba a la alternativa C es experiencia de uso (dimensiones 10 y 11), y
el criterio del equipo la subordina explícitamente al coste permanente. Ese coste está
medido y es concreto: 7 paquetes a vigilar de por vida, 7,5 MB, +78 ms en cada invocación, y
un acoplamiento que **crece con cada comando** en lugar de mantenerse constante.

La dimensión 8 es la decisiva a dos años vista: con B, añadir el comando número quince no
añade ni una línea de acoplamiento; con C, añade dos.

---

## Riesgos

Clasificados según el efecto real de renunciar a la alternativa C. Cada uno lleva la
evidencia que lo sostiene — no hay riesgos declarados por intuición.

| Categoría | Riesgo | Severidad | Evidencia | Mitigación |
|-----------|--------|-----------|-----------|------------|
| **Funcional** | Que `argparse` no cubra algún tipo de argumento necesario | **Ninguna** | El prototipo implementa la superficie completa (5 comandos, rutas, textos, valores por defecto) y funciona | No aplica |
| **Mantenibilidad** | **Que el parser y el dataclass se desincronicen**: alguien añade `--nueva-opcion` al parser y olvida el campo, o al revés. `mypy` no lo detecta porque el `Namespace` es `Any` | **Media — es el riesgo real de esta decisión** | Dimensión 5: `mypy --strict` no ve nada dentro del `Namespace`. La frontera tipada protege *aguas abajo*, no la frontera misma | **Test de gobernanza obligatorio**: comparar los `dest` declarados en el parser contra los campos del dataclass y fallar si difieren. Es la única mitigación con evidencia objetiva y por eso es la única que este ADR impone (ver HU-163) |
| **DX** | Sin autocompletado de shell | Baja | Dimensión 10 | Ninguna dentro del criterio: cualquier solución añade una dependencia. Se asume |
| **DX** | La ayuda de cada opción se escribe a mano (`help=`) en vez de derivarse del docstring | Baja | Dimensión 11; ya contabilizado en las 39 líneas | Se asume. Es trabajo lineal y visible en revisión |
| **DX** | Ayuda visualmente más sobria | **Ninguna medible** | Comparadas ambas salidas: la de `argparse` es correcta y legible. En la consola de la máquina de referencia, los recuadros de la alternativa C se degradan a `+-` por codificación | No aplica |
| **Rendimiento** | — | **Riesgo invertido** | Dimensión 3: la decisión **ahorra 78 ms por invocación**. Relevante para el presupuesto de 60 s del smoke E2E (HU-185) | No aplica |
| **Compatibilidad** | Cambios de comportamiento de `argparse` entre versiones de Python | Baja | `argparse` es stdlib con política de compatibilidad de CPython; el proyecto fija `requires-python = ">=3.12"` y `uv.lock` fija el intérprete | Los gates de HU-163 corren sobre la versión fijada |
| **Deuda técnica** | Que la CLI crezca hasta que `argparse` a mano resulte verboso | Baja hoy | Con 5 comandos son 39 líneas. **Extrapolar más allá sería especular, no medir** | **Umbral de reapertura explícito**, abajo |

---

## Impacto futuro

**Umbral de reapertura de este ADR.** Se reabre —con mediciones nuevas, no con opiniones— si
se cumple **cualquiera** de estas condiciones objetivas:

1. La CLI supera **15 comandos**, o aparece un comando con subcomandos anidados o flags
   mutuamente excluyentes.
2. El bloque de construcción del parser supera **150 líneas** (hoy: 39 para 5 comandos).
3. El autocompletado de shell pasa a ser un requisito de producto, no una comodidad.

Mientras ninguna se cumpla, la decisión se mantiene sin revisarla.

**Coste de revertir.** Medido: 2 funciones. La frontera tipada es lo que hace barata la
marcha atrás — el resto del sistema nunca ve `argparse`, ve un dataclass propio. Esa
propiedad **es** el beneficio estructural que justifica la decisión, y es la razón por la que
el umbral de reapertura no da miedo.

---

## Consecuencias

**Positivas**
- El proyecto se mantiene con **dos dependencias de producción** (`numpy`,
  `opencv-python-headless`). La CLI no añade ninguna.
- Superficie de actualización y de cadena de suministro: **cero paquetes nuevos que vigilar**.
- `mypy --strict` verifica el camino completo desde el argumento parseado hasta el dominio.
- Arranque 2,7× más rápido, con efecto directo sobre el presupuesto del smoke E2E.
- El acoplamiento a la librería queda confinado a dos funciones y **no crece**.

**Negativas, asumidas conscientemente**
- Sin autocompletado de shell.
- El `help=` de cada opción se escribe a mano.
- Aparece un riesgo nuevo —la desincronización parser/dataclass— que **no existía** con la
  alternativa C, donde la firma era la declaración. Se neutraliza con un test de gobernanza
  obligatorio; sin ese test, la decisión no está completa.

**Neutrales**
- Las restricciones que el equipo había planteado para el caso de adoptar un framework de
  terceros (capa delgada, cero lógica de negocio en `cli/`, salida persistida determinista)
  siguen vigentes tal cual: no dependían de la librería elegida. Quedan documentadas en
  `docs/blueprint/arquitectura.md`.

---

## Anexo — reproducir las mediciones

```bash
cd items/HU-162/insumos/cli-bench
uv venv .venv-typer && VIRTUAL_ENV=.venv-typer uv pip install typer mypy

# Dimensión 5 — quién detecta el error de tipo deliberado
VIRTUAL_ENV=.venv-typer uv run --no-project mypy --strict error_argparse.py         # Success  (A no lo detecta)
VIRTUAL_ENV=.venv-typer uv run --no-project mypy --strict error_argparse_tipado.py  # 1 error  (B sí)
VIRTUAL_ENV=.venv-typer uv run --no-project mypy --strict error_typer.py            # 1 error  (C sí)

# Dimensión 2 — huella en disco
du -sk .venv-typer/Lib/site-packages/pygments                                       # 5077 KB

# Dimensión 3 — arranque
python -c "import argparse"   # 44,6 ms de proceso completo (mediana de 5)
python -c "import typer"      # 122,3 ms

# Argumento refutado nº 2 — ambas ayudas dependen del ancho
COLUMNS=60  python cli_argparse.py ingest --help | wc -c   # 341
COLUMNS=120 python cli_argparse.py ingest --help | wc -c   # 279
COLUMNS=60  python cli_typer.py    ingest --help | wc -c   # 856
COLUMNS=120 python cli_typer.py    ingest --help | wc -c   # 1575
```
