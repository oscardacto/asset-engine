# Índice de insumos — HU-162

| Archivo | Qué es | Por qué importa |
|---------|--------|-----------------|
| `cli-bench/` | Tres prototipos funcionalmente equivalentes de la CLI, sus variantes con error de tipo deliberado y las ayudas capturadas a 60 y 120 columnas | Es la evidencia reproducible sobre la que se decidió ADR-005. Sin ella el ADR sería opinión |

El entorno con la dependencia de terceros se creó aislado y desechable: **no se agregó nada
a `pyproject.toml` ni a `uv.lock`**.
