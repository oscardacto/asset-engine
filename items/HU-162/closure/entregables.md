# Entregables — HU-162

## Evidencia contra los criterios de aceptación

| CA | Resultado | Evidencia |
|----|-----------|-----------|
| CA-1 `--version` imprime y sale con 0 | ✅ | `test_version_imprime_y_sale_con_cero` + verificado en terminal |
| CA-2 Sin comando: ayuda y `2`, sin traza | ✅ | `test_sin_comando_muestra_la_ayuda_y_no_una_traza` |
| CA-3 Comando inexistente: uso y `2` | ✅ | `test_un_comando_inexistente_sale_con_error_de_uso` |
| CA-4 Las globales producen un `RunContext` tipado | ✅ | `TestContextoGlobal` (3 tests) |
| CA-5 **Parser y contrato sincronizados, por comando** | ✅ | `TestSincroniaEntreParserYContrato`, 6 tests parametrizados. **Verificado por inyección** |
| CA-6 `mypy --strict` limpio sobre `cli/` | ✅ | 36 archivos, sin hallazgos |
| CA-7 `argparse` solo en `cli/`; `core/` no lo importa | ✅ | 2 reglas nuevas en el test de arquitectura |
| CA-8 Entrada inválida → mensaje accionable y `3`, sin traza | ✅ | 2 tests: el código y que el mensaje dice qué hacer |
| CA-9 Excepción inesperada propaga su traza | ✅ | `test_una_excepcion_inesperada_propaga_su_traza` |
| CA-10 Cada código de salida en su escenario | ✅ | `TestCodigosDeSalida` + `TestTraduccionDeErrores` parametrizado |
| CA-11 `--log-file` en ruta larga escribe bytes reales | ✅ | `test_el_rastro_a_archivo_funciona_en_una_ruta_larga` (>260 car.) |
| CA-12 Cobertura ≥80% en `cli/` y batería verde | ✅ | **100%** en los 10 módulos de `cli/` y en `pipeline/`; 461 passed + 1 skipped; total 98% |
| CA-13 Trazabilidad | ✅ | gate-log completo, incluidos los dos intentos de gate |

**Resultado: 13/13 · 0 fallidos · sin rework.**

## Verificación de que el guardián no pasa en vacío

Inyectada una opción `--dry-run` en el parser de `run` **sin** su campo en el contrato:
fallan los 2 tests de sincronía y nombran el campo huérfano (`dry_run`). Es exactamente el
fallo que el verificador de tipos no puede detectar, y la única mitigación que ADR-005
impone.

## Comprobación fuera de los tests

```
uv run media-optimizer --version     -> media-optimizer 0.1.0
uv run media-optimizer --help        -> 3 comandos, 6 opciones globales
uv run media-optimizer run --help    -> {ingest,analyze,develop,select,reel,all}
```

La lista de etapas de la ayuda **sale del registro**, no está escrita en `cli/`.

## Preguntas abiertas de la spec — ratificadas

- **P-2 (`--workspace` y `--profile` globales):** ratificada; son el contexto del run, no
  parámetros de una etapa.
- **P-3 (el registro declara la superficie completa desde el primer día):** ratificada. Cada
  entrada gana su ejecutor con su HU; mientras tanto avisa con claridad en vez de fingir que
  la etapa no existe.
