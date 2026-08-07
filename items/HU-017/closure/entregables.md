# Entregables — HU-017

| CA | Resultado | Evidencia |
|----|-----------|-----------|
| CA-1 Catálogo byte-idéntico entre corridas | ✅ | `test_dos_corridas_producen_el_mismo_catalogo_byte_a_byte` |
| CA-2 Resumen: encontrados/aceptados/apartados/duplicados | ✅ | `test_el_resumen_cuenta_lo_que_paso` + validado en lote real |
| CA-3 Códigos 0 / 4 / 3 / 3 por escenario | ✅ | 4 tests + código 4 verificado en el lote real |
| CA-4 Originales intactos, comprobado | ✅ | 2 tests, incluida la rama de fallo por inyección |
| CA-5 `StageReport` medido y en el rastro | ✅ | `TestObservabilidad` |
| CA-6 Disponibilidad derivada del ejecutor | ✅ | `TestDisponibilidadDerivada` |
| CA-7 Medidas orientadas (EXIF aplicado) | ✅ | `test_las_medidas_del_catalogo_son_las_orientadas` |
| CA-8 Gobernanza verde | ✅ | tests de arquitectura sin cambios |
| CA-9 Cobertura ≥80% y batería verde | ✅ | `stages.py` 95%; 478 passed + 1 skipped; total 99% |
| CA-10 Trazabilidad | ✅ | gate-log |

**Resultado: 10/10 · 0 fallidos · 1 rework registrado (HU-162).**

## Validación con medios reales
109 archivos del cliente → 102 al catálogo, 7 videos apartados con causa, 16 grupos de
duplicados detectados, salida 4 (PARTIAL). `catalog.json` legible y determinista.
