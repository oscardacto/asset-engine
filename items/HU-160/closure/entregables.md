# Entregables — HU-160

## Integración
| Merge | Rama | Descripción |
|-------|------|-------------|
| `a857a8e` | `feature/HU-160-business-profile` → `develop` | Contrato `BusinessProfile` + `OutputIntent` + `OutputFormat` + `ScoringWeights` |

## Evidencia contra los criterios de aceptación

| CA | Resultado | Evidencia |
|----|-----------|-----------|
| CA-1 Inmutable y de orden estable | ✅ | `TestInmutabilidad` (3) + `TestDeterminismo` (4) |
| CA-2 `format_for` responde o devuelve `None` | ✅ | 2 tests, incluido el perfil que no produce portada |
| CA-3 `weights_for` devuelve grupo vacío si no cubre la intención | ✅ | `test_una_intencion_sin_pesos_devuelve_un_grupo_vacio` |
| CA-4 `threshold` con default | ✅ | `test_un_umbral_ausente_devuelve_el_valor_indicado` |
| CA-5 Aspecto derivado (`1080×1350` ⇒ 0.8) | ✅ | `test_el_aspecto_se_deduce_de_las_dimensiones` |
| CA-6 Intención duplicada ⇒ `ValueError` | ✅ | 2 tests (formatos y pesos) |
| CA-7 Peso negativo/NaN/inf falla; `0.0` válido | ✅ | parametrizado sobre 3 valores + test del cero |
| CA-8 Identificadores vacíos fallan | ✅ | 5 tests (nombre, versión, métrica, umbral, ambiente) |
| CA-9 **Vertical distinta cabe sin tocar el módulo** | ✅ | `bar_nocturno`: exposición objetivo negativa, sin feed, movimiento pesando más que nitidez. Más el guardián de vocabulario, **verificado inyectando la violación** |
| CA-10 `core/` sigue sin IO | ✅ | test de arquitectura verde |
| CA-11 Cobertura ≥95% y batería verde | ✅ | **100%** en el módulo; 354 passed + 1 skipped; total 98% |
| CA-12 Trazabilidad | ✅ | gate-log completo |

**Resultado: 12/12 · 0 fallidos · sin rework.**

## Preguntas abiertas de la spec — ratificadas
- **P-1 (`OutputIntent` cerrado):** ratificada. El test del bar nocturno construye un perfil
  de vertical opuesta sin necesitar una intención nueva. Se re-evalúa en HU-132.
- **P-2 (los pesos no se normalizan aquí):** ratificada. `test_los_pesos_no_tienen_que_sumar_uno`
  documenta la decisión para HU-070.

## Commits
- `0d2b8c1` — DEV: contrato + 52 tests
- `a857a8e` — merge a `develop`
