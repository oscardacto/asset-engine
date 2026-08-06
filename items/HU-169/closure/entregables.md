# Entregables — HU-169

## Integración
| Rama | Descripción |
|------|-------------|
| `feature/HU-169-determinismo` → `develop` | Utilidades de orden estable + arreglo del defecto de reproducibilidad en `QualityReport` |

## Evidencia contra los criterios de aceptación

| CA | Resultado | Evidencia |
|----|-----------|-----------|
| CA-1 NFD y NFC son el mismo texto | ✅ | `test_dos_escrituras_del_mismo_nombre_son_el_mismo_texto` |
| CA-2 Ordena igual venga de donde venga | ✅ | 2 tests: el correcto **y** el que demuestra que sin normalizar sí cambiaría |
| CA-3 Los flags iteran siempre igual | ✅ | `test_los_flags_iteran_siempre_en_el_mismo_orden` |
| CA-4 Dos procesos, mismos bytes | ✅ | `TestReproducibilidadEntreProcesos` — 4 semillas de hash, una sola salida |
| CA-5 Duplicados descartados; `in` funciona | ✅ | 2 tests |
| CA-6 Ningún contrato de `core/` expone conjuntos | ✅ | `TestGuardianDeContratos`, recorre `core.__all__` |
| CA-7 `stable_order_by` sobre objetos | ✅ | `test_ordena_objetos_por_una_clave_de_texto` |
| CA-8 Colección vacía válida | ✅ | `test_una_coleccion_vacia_no_es_un_error` |
| CA-9 `core/` sin IO | ✅ | test de arquitectura verde |
| CA-10 Cobertura ≥95% y batería verde | ✅ | `determinism.py` **100%**, `quality_report.py` **100%**; 422 passed + 1 skipped |
| CA-11 Rework de HU-158 registrado | ✅ | evento `rework` en el gate-log, con motivo y forma de detección |

**Resultado: 11/11 · 0 fallidos.**

## Verificación de que los guardianes no pasan en vacío
Restaurado `flags: frozenset[str]` en producción, fallan **3 pruebas**:
- `test_dos_procesos_con_semillas_distintas_dan_los_mismos_bytes`
- `test_el_orden_es_el_alfabetico_esperado`
- `test_ningun_contrato_de_core_expone_un_conjunto` → nombra al infractor: `QualityReport.flags: frozenset[str]`

## Preguntas abiertas de la spec — ratificadas
- **P-1 (`determinism` dentro de `core/`):** ratificada. Es puro y lo consumen los propios
  contratos de `core/`; ponerlo arriba obligaría al dominio a importar un módulo externo.
- **P-2 (cuenta como rework de HU-158):** ratificada y registrada. El contrato se cerró con
  un defecto latente de reproducibilidad; que no rompiera nada todavía no lo vuelve correcto.
