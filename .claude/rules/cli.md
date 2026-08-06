---
description: Patrón obligatorio de la capa CLI — argparse con frontera tipada (ADR-005).
paths:
  - "src/media_optimizer/cli/**/*.py"
  - "tests/cli/**/*.py"
---

# Capa CLI — patrón obligatorio

Fijado por **ADR-005**. Aplica a esta CLI y a cualquier otra que el proyecto añada.

## Regla dura 1 — solo la biblioteca estándar

**`argparse` de la biblioteca estándar. Ninguna librería de terceros para parsear
argumentos, formatear ayuda o colorear la salida.** El proyecto tiene dos dependencias de
producción y la CLI no añade ninguna.

## Regla dura 2 — las etapas son datos, no comandos

La superficie es **`run <etapa>`, `report <tipo>`, `label`**. Un comando nuevo por cada
etapa del pipeline haría que la CLI creciera con el producto, y ADR-005 se reabre a los 15
comandos.

**Ningún módulo de `cli/` puede llevar escrita a mano una lista de etapas o de reportes.**
Los valores válidos se piden a `pipeline/registry.py`, que es la única fuente. Añadir una
etapa se hace ahí y `cli/` no se toca. Lo verifica la regla A-6 de `arquitectura.md`.

**Ninguna etapa lleva banderas propias.** Sus parámetros son datos del perfil de negocio
(charter §3): un `--clahe-clip` sería criterio estético fuera del perfil. Toda etapa recibe
lo mismo — workspace, perfil y opcionalmente un origen—, y por eso la etapa es un argumento
posicional con `choices`, no un subparser anidado.

## El patrón: frontera tipada

`argparse` devuelve un `Namespace` cuyos atributos son `Any`. **`mypy --strict` no ve nada
dentro de él** — se midió: con un error de tipo deliberado reporta *"Success: no issues
found"*. Por eso el `Namespace` no puede salir de la función que lo produce.

Cada comando se escribe en cuatro piezas, siempre en este orden:

### 1 · Dataclass congelado — lo que el comando recibió

```python
@dataclass(frozen=True, slots=True)
class IngestArgs:
    """Lo que el usuario pidió, ya con tipos que mypy puede verificar."""

    source: Path
    workspace: Path
    profile: str
```

Es el **contrato de entrada del comando**. Congelado y con `slots=True`, como todos los
contratos del proyecto. Nunca contiene tipos de `argparse`.

### 2 · Construcción del parser — aislada

```python
def build_parser() -> argparse.ArgumentParser: ...
```

Es una de las **dos únicas funciones** de todo el proyecto que pueden mencionar `argparse`.

### 3 · Conversión y validación — la frontera

```python
def parse_ingest(namespace: argparse.Namespace) -> IngestArgs:
    """Convierte el Namespace sin tipos en un contrato verificable."""
```

La segunda y última función que menciona `argparse`. Aquí se convierte **cada** campo
explícitamente (`Path(...)`, `str(...)`) y se valida lo que solo se puede validar aquí.

**Validar aquí ≠ validar reglas de negocio.** Aquí solo se comprueba lo que hace que el
argumento sea *utilizable*: que una ruta exista, que un valor esté entre los permitidos.
Que una foto sea publicable lo decide el dominio.

### 4 · Ejecución — sin rastro de la librería

```python
def run_ingest(args: IngestArgs) -> ExitCode:
    """Invoca el dominio y traduce el resultado a código de salida."""
```

Su firma **no menciona `argparse`**, y por eso el dominio nunca lo ve.

## Test de gobernanza obligatorio

Es el único riesgo real que ADR-005 identificó: **el parser y el dataclass pueden
desincronizarse** —alguien añade `--nueva-opcion` y olvida el campo— y `mypy` no lo detecta,
porque el `Namespace` es `Any`. La frontera tipada protege aguas abajo, no la frontera misma.

Por cada comando, un test que compare **los `dest` declarados en el parser contra los campos
del dataclass** y falle si difieren. Sin ese test, el patrón está incompleto.

## Prohibiciones verificadas por la batería

| # | Prohibición | Cómo se verifica |
|---|-------------|------------------|
| 1 | `argparse` fuera de `cli/` | Test de arquitectura: ningún módulo fuera de `cli/` lo importa |
| 2 | `core/` importando `argparse` | Test de arquitectura, lista de importaciones prohibidas del dominio |
| 3 | Lógica de negocio en `cli/` | Un comando de más de ~15 líneas es la señal; revisión de PR |
| 4 | `print()` | Regla `T20` de ruff, ya activa. La consola se escribe con el rastro de `logs` o con el escritor del comando |
| 5 | Escribir a disco sin la capa | Test de arquitectura de ADR-004 |

## Códigos de salida

Un enumerado propio (`ExitCode`), nunca números sueltos. `2` está reservado por `argparse`
para errores de uso y **no puede reutilizarse para otra cosa**.

## Errores

Un error del dominio (`MediaOptimizerError`) se traduce a un mensaje accionable y a su
código de salida. **Nunca se muestra un stacktrace al usuario por un fallo esperable.** Un
error inesperado sí revienta con su traza completa: envolverlo lo escondería.
