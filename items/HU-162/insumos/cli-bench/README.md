# Banco de medición del ADR-005

Prototipos funcionalmente equivalentes de la CLI prevista (5 comandos, mismos argumentos),
usados para medir en vez de opinar. **No son código del proyecto** — viven en `insumos/`
como evidencia reproducible del ADR.

| Archivo | Qué es |
|---|---|
| `cli_argparse.py` | argparse idiomático, leyendo del `Namespace` |
| `cli_argparse_tipado.py` | argparse + frontera tipada (dataclass congelado) |
| `cli_typer.py` | Typer idiomático con `Annotated` |
| `error_*.py` | Los tres, con un error de tipo deliberado, para ver cuál detecta `mypy --strict` |
| `*_help_60.txt` / `*_help_120.txt` | Ayuda renderizada a 60 y 120 columnas |

Resultado clave: `mypy --strict` **no** detecta el error en `error_argparse.py` (dice
"Success"), pero **sí** en `error_argparse_tipado.py` y en `error_typer.py`. Es decir, el
tipado no es un argumento que distinga a Typer: cuesta 5 líneas de argparse.

El entorno con `typer` se creó aislado y desechable; **no se agregó nada a `pyproject.toml`**.
