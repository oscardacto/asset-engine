# Entregables — HU-168

## Integración
| Merge | Rama | Descripción |
|-------|------|-------------|
| `7f5af6d` | `feature/HU-168-stage-report` → `develop` | `StageReport` + `ReproducibleStageSummary` |

## Evidencia contra los criterios de aceptación

| CA | Resultado | Evidencia |
|----|-----------|-----------|
| CA-1 Inmutable con los cuatro campos del mandato | ✅ | `TestLosCuatroCamposObligatorios` (2) + `test_la_ficha_no_se_puede_alterar` |
| CA-2 `reproducible_part()` es otro tipo, sin tiempo ni memoria | ✅ | `test_la_parte_reproducible_no_trae_tiempo_ni_memoria` |
| CA-3 Tiempos distintos ⇒ partes reproducibles iguales | ✅ | `test_dos_corridas_con_tiempos_distintos_comparan_igual` |
| CA-4 Duración/memoria negativas fallan; cero es válido | ✅ | parametrizado sobre 4 valores + test del cero |
| CA-5 Score no finito o sin nombre falla | ✅ | 3 tests parametrizados + 1 |
| CA-6 Etapa sin nombre falla | ✅ | `test_una_etapa_sin_nombre_falla` |
| CA-7 Scores ordenados y de solo lectura | ✅ | `TestDeterminismoEInmutabilidad` (4) |
| CA-8 Etapa sin transformaciones ni scores es válida | ✅ | `test_una_etapa_que_no_transforma_ni_puntua_es_valida` |
| CA-9 `core/` sigue sin IO | ✅ | test de arquitectura verde |
| CA-10 Cobertura ≥95% y batería verde | ✅ | **100%** en el módulo; 379 passed + 1 skipped; total 98% |
| CA-11 Trazabilidad | ✅ | gate-log completo |

**Resultado: 11/11 · 0 fallidos · sin rework.**

## Preguntas abiertas de la spec — ratificadas
- **P-1 (memoria en bytes enteros):** ratificada. Sin redondeos entre la medida y el dato.
- **P-2 (la parte reproducible no incluye tiempo redondeado):** ratificada. Redondear no
  vuelve determinista un tiempo; solo hace la intermitencia más rara y más difícil de
  diagnosticar. Comparar rendimiento contra presupuesto es HU-165, con tolerancia explícita.

## Commits
- `f376d59` — DEV: contrato + 25 tests
- `7f5af6d` — merge a `develop`
