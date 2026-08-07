# HU-162 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/pipeline/registry.py` | Las etapas y los reportes **como datos**: `StageEntry`, `ReportEntry` y sus consultas |
| `src/media_optimizer/cli/main.py` | Parser raíz, opciones globales, despacho, traducción de errores |
| `src/media_optimizer/cli/context.py` | `RunContext`: el contexto del run, ya con tipos verificables |
| `src/media_optimizer/cli/exit_codes.py` | `ExitCode` como enumerado |
| `src/media_optimizer/cli/errors.py` | Excepción del dominio → mensaje accionable + código |
| `src/media_optimizer/cli/console.py` | Lo que lee la persona, separado del rastro estructurado |
| `src/media_optimizer/cli/commands/` | `run`, `report`, `label` — las cuatro piezas del patrón en cada uno |
| `tests/cli/test_main.py` | 39 tests |
| `tests/test_arquitectura.py` | 2 reglas nuevas: `argparse` solo en `cli/`; sin listas del registro copiadas a mano |

**La CLI no crece con el pipeline.** Las etapas y los reportes viven en el registro y la
interfaz tiene tres verbos fijos: añadir una etapa es añadir una línea al registro, y
`cli/` no se toca. Es lo que mantiene el parser pequeño indefinidamente.

**El riesgo que había que neutralizar no era el parseo.** `argparse` devuelve un objeto
cuyos atributos no tienen tipo, y el verificador no ve nada dentro: si alguien añade una
opción y olvida el campo del contrato, **nada lo detecta**. Por cada comando hay un test que
compara los argumentos declarados contra los campos del contrato. Se comprobó inyectando la
desincronización —una opción `--dry-run` sin campo— y los dos tests fallan nombrando el
campo huérfano.

**Los códigos de salida existen por el caso normal, no por el excepcional.** El programa está
hecho para que una foto dañada se aparte y el lote siga, así que terminar con fallos
parciales es lo habitual. Con solo "bien" y "mal" habría que elegir entre ocultar doce fotos
en cuarentena o alarmar cuando el resultado sirve.

**Dos hallazgos durante la implementación:**

- Reexportar `main` desde `cli/__init__.py` **tapaba el módulo con la función del mismo
  nombre**: al pedir el módulo se obtenía la función. Se quitó el reexport y el punto de
  entrada apunta directo a `cli.main:main`.
- La primera versión de la regla que prohíbe copiar el registro buscaba los nombres como
  texto suelto, y marcaba el nombre del comando `run` —que coincide con el del reporte
  `run`—. Ahora mira **colecciones literales**, que es lo que la regla realmente prohíbe.

Evidencia DEV: **461 tests passed (39 nuevos) · `cli/` y `pipeline/` al 100%** · ruff y mypy
limpios · `media-optimizer --help` verificado en la terminal.
