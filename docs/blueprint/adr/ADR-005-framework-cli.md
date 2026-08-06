# ADR-005 — Framework de la CLI: `argparse` vs `Typer`

- **Estado:** **Pendiente de decisión arquitectónica** — el análisis está cerrado; falta la decisión del equipo
- **Fecha:** 2026-08-06 (v2 — comparativo con evidencia medida; la v1 fue prescriptiva y se descarta)
- **Origen:** HU-162 (backlog E7) · bloquea HU-017, HU-037, HU-184
- **Decisores:** equipo técnico (@oscardacto) · medición y análisis: Claude (orquestador-ejecutor ASDD)

---

## Criterio de decisión

Fijado por el equipo el 2026-08-06:

> **Minimizar la complejidad permanente.** Una dependencia solo se incorpora si aporta un
> beneficio **estructural** superior al coste de mantenerla durante toda la vida del
> proyecto. No se optimiza la velocidad de escribir código, sino la mantenibilidad del
> sistema dentro de dos años.

Todo lo que sigue se evalúa contra ese criterio, no contra comodidad de desarrollo.

## Cómo se midió

Se construyeron **tres prototipos funcionalmente equivalentes** de la CLI real prevista
(5 comandos — `ingest`, `analyze`, `develop`, `select`, `run` — cada uno con un argumento
posicional `carpeta: Path` y las opciones `--workspace: Path` y `--profile: str`, más
`--version`):

| Prototipo | Qué es |
|---|---|
| `cli_argparse.py` | argparse idiomático, leyendo del `Namespace` |
| `cli_argparse_tipado.py` | argparse + frontera tipada: el `Namespace` se convierte en un dataclass congelado |
| `cli_typer.py` | Typer idiomático con `Annotated` |

Medidos en la máquina de referencia (Windows 10 Pro 19045, Python 3.13.2), con `typer`
instalado en un entorno virtual **aislado y desechable** — no se agregó nada a
`pyproject.toml`. Los prototipos y sus salidas están en `items/HU-162/insumos/cli-bench/`.

---

## Matriz técnica

| # | Dimensión | `argparse` (stdlib) | `Typer` | Gana |
|---|-----------|---------------------|---------|------|
| 1 | **Dependencias transitivas** | **0** | **7**: `typer`, `rich`, `pygments`, `markdown-it-py`, `mdurl`, `shellingham`, `colorama`, `annotated-doc` | argparse |
| 2 | **Tamaño en disco** | 0 KB (ya está en Python) | **7 512 KB**, de los cuales **5 077 KB son `pygments`** — un resaltador de sintaxis, en una CLI que nunca resalta sintaxis | argparse |
| 3 | **Arranque** (mediana de 5, proceso completo) | **44,6 ms** | **122,3 ms** (**2,7×**) | argparse |
| 4 | **Líneas de código propio** (5 comandos) | 23 (sin tipar) · **39** (tipado) | **34** | Typer, por **5 líneas** |
| 5 | **`mypy --strict` detecta un error de tipo en el argumento parseado** | ❌ **No**, en la versión ingenua: `args.carpeta` es `Any` y mypy reporta *"Success: no issues found"* con un error deliberado presente<br>✅ **Sí**, en la versión tipada | ✅ **Sí**: `error: Argument 1 to "contar" has incompatible type "Path"; expected "int"` | **Empate** si argparse se tipa |
| 6 | **Puntos de acoplamiento a la librería** | **2 líneas**, ambas dentro de `construir_parser()` y `leer()` | **9 líneas**: 4 referencias `typer.*` + **1 decorador `@app.command` por comando** | argparse |
| 7 | **Funciones cuya firma menciona la librería** | **1** — y su parámetro es un dataclass propio, no un tipo de argparse | **5** — una por comando: `carpeta: Annotated[Path, typer.Argument(...)]` | argparse |
| 8 | **Coste de migración futura** | Reescribir 2 funciones. El resto del sistema ve un `Invocacion` propio | Reescribir las 5 firmas + los 5 decoradores; crece **linealmente con cada comando nuevo** | argparse |
| 9 | **Riesgo de lock-in** | Nulo: `argparse` es stdlib con garantía de compatibilidad de Python | Medio: el acoplamiento vive **en la firma de cada comando**, que es justo donde la restricción del equipo pide que no esté | argparse |
| 10 | **Reproducibilidad de la salida persistida** | **Ninguna de las dos la afecta** — ver nota abajo | Igual | Empate |
| 11 | **Superficie de actualización** | 0 paquetes que vigilar | 7 paquetes con su propio calendario de versiones y CVEs | argparse |
| 12 | **Calidad de la ayuda** | Correcta y seca | Mejor estructurada (paneles, colores, `[default: …]`, `[required]`). **Pero** en la consola de la máquina de referencia los bordes salen como `+-` en vez de `┌─` | Typer |
| 13 | **Autocompletado de shell** | No lo trae | Sí, de serie | Typer |
| 14 | **Ayuda por comando desde el docstring** | Hay que escribirla aparte (`help=…`) | Automática | Typer |

### Nota que corrige un argumento de la v1 de este ADR

La v1 sostenía que `rich` amenaza el determinismo porque formatea según el ancho del
terminal. **Se midió y el argumento estaba mal planteado:** la ayuda de Typer cambia con el
ancho (856 → 1 575 bytes entre 60 y 120 columnas), **pero la de argparse también** (341 → 279
bytes). Ninguna de las dos librerías escribe la salida persistida del pipeline — esa la
genera código propio. **El determinismo no distingue entre las dos opciones**, y presentarlo
como ventaja de una era un argumento inflado. Se retira.

---

## Lectura de la evidencia contra el criterio

**El único beneficio estructural que Typer reclamaba era el tipado**, y la medición lo
disuelve: argparse recupera la verificación completa de `mypy --strict` convirtiendo el
`Namespace` en un dataclass congelado, y eso cuesta **5 líneas más que Typer** (39 vs 34).

Lo que queda a favor de Typer —ayuda más bonita, autocompletado, menos ceremonia— es
**experiencia de desarrollo y de uso, no estructura**. Son beneficios reales, pero el
criterio del equipo los subordina explícitamente al coste permanente.

Y el coste permanente es concreto y medido:

- **7 paquetes** a vigilar durante toda la vida del proyecto, de los cuales el más pesado
  (5 MB de `pygments`) existe para resaltar sintaxis que esta CLI nunca va a mostrar.
- **+78 ms en cada invocación.** Un comando que se corre decenas de veces al día paga eso
  siempre; y el smoke test E2E de HU-185 tiene un presupuesto de 60 s.
- **El acoplamiento vive en la firma de cada comando** y crece con cada comando nuevo. La
  restricción del equipo —*"ninguna lógica de negocio puede depender de Typer"*— se cumple
  mejor con la opción cuyo punto de entrada al dominio recibe un dataclass propio (1 firma
  acoplada) que con la que acopla 5 y sumando.

**Dicho al revés:** si Typer costara 0 dependencias, ganaría por las dimensiones 12–14. Con
7, y con el tipado empatado, no hay beneficio estructural que compense.

## Recomendación

**Opción A — `argparse` con frontera tipada explícita** (el prototipo
`cli_argparse_tipado.py`): `argparse` construye el parser, y su resultado se convierte
inmediatamente en un dataclass congelado `Invocacion` que es lo único que el resto del
sistema ve.

Esa frontera no es ceremonia: es la que hace que `mypy --strict` verifique lo que el usuario
realmente escribió, y la que deja el acoplamiento a la librería confinado a dos funciones.

**Esta recomendación invierte la de la v1 de este ADR.** La v1 recomendaba Typer sin haber
medido nada: asumía que argparse renunciaba al tipado (falso, cuesta 5 líneas), que `rich`
amenazaba el determinismo (falso, ambas dependen del ancho) y no contaba ni el arranque ni el
acoplamiento por comando. Con las tres correcciones, la comparación se invierte.

### Si el equipo decide Typer de todos modos

Las restricciones fijadas por el equipo se traducen así, y son verificables:

1. `cli/` extremadamente delgada: cada comando parsea, construye un dataclass propio e invoca
   al dominio. **Cero lógica de negocio.** Un comando de más de ~10 líneas es la señal.
2. **Ningún módulo fuera de `cli/` importa Typer.** Verificable ampliando
   `tests/test_arquitectura.py`, que ya sabe detectar importaciones prohibidas por capa.
3. `rich` nunca en salida persistida: todo reporte a archivo lo genera código propio.
4. La salida persistida se compara byte a byte en golden tests, sin excepción.

## Consecuencias

**Si se adopta argparse (recomendado)**
- El proyecto se mantiene con **2 dependencias de producción** (`numpy`, `opencv-headless`).
- Coste asumido: sin autocompletado; la ayuda es más seca; hay que escribir el `help=` de
  cada opción a mano. Ninguno es estructural y los tres son reversibles.
- Si en el futuro la CLI creciera mucho (20+ comandos, argumentos compuestos), migrar a
  Typer costaría reescribir 2 funciones — **este ADR se reabre entonces, con datos nuevos**.

**Si se adopta Typer**
- 7 paquetes al lock, +78 ms por invocación, y las 4 restricciones de arriba pasan a ser
  reglas verificadas por test, no buenas intenciones.

## Qué falta para cerrar

Solo la decisión del equipo. Ambos caminos están medidos y HU-162 puede implementarse en
cualquiera de los dos sin retraso.

## Anexo — reproducir las mediciones

```bash
uv venv .venv-typer && VIRTUAL_ENV=.venv-typer uv pip install typer mypy
VIRTUAL_ENV=.venv-typer uv run --no-project mypy --strict error_argparse.py         # Success (no lo detecta)
VIRTUAL_ENV=.venv-typer uv run --no-project mypy --strict error_argparse_tipado.py  # 1 error (sí lo detecta)
VIRTUAL_ENV=.venv-typer uv run --no-project mypy --strict error_typer.py            # 1 error (sí lo detecta)
du -sk .venv-typer/Lib/site-packages/pygments                                       # 5077 KB
COLUMNS=60 python cli_typer.py ingest --help | wc -c                                # 856
COLUMNS=120 python cli_typer.py ingest --help | wc -c                               # 1575
```
