# Entregables — HU-156

## Integración
| Merge | Rama | Descripción |
|-------|------|-------------|
| (ver `git log`) | `feature/HU-156-logging-estructurado` → `develop` | Rastro JSON-lines + handler que pasa por la capa + regla de gobernanza ampliada |

## Evidencia contra los criterios de aceptación

| CA | Resultado | Evidencia |
|----|-----------|-----------|
| CA-1 Cada registro es JSON válido | ✅ | `test_cada_evento_es_una_linea_de_json_valido` |
| CA-2 Claves ordenadas | ✅ | `test_las_claves_salen_ordenadas` |
| CA-3 Los `extra` aparecen | ✅ | `test_los_datos_adjuntos_aparecen_en_la_linea` |
| CA-4 Un `extra` no serializable no rompe la línea | ✅ | `test_un_dato_no_serializable_no_rompe_la_linea` |
| CA-5 Un `extra` no puede falsear un reservado | ✅ | `test_un_dato_del_llamador_no_puede_falsear_el_nivel` |
| CA-6 Ruta larga escribe **bytes reales** | ✅ | `test_un_log_en_ruta_larga_guarda_bytes_reales` (>260 car.) |
| CA-7 `CON.log`/`NUL.log`/`COM1.log` escriben **bytes reales** | ✅ | parametrizado sobre los 3; lee el archivo y valida el JSON |
| CA-8 El handler crea la carpeta que falte | ✅ | `test_el_handler_crea_la_carpeta_que_falte` |
| CA-9 Configurar dos veces no duplica | ✅ | `test_configurar_dos_veces_no_duplica_lineas` |
| CA-10 Acentos sin escapar | ✅ | `test_los_acentos_se_escriben_tal_cual` |
| CA-11 La regla detecta `logging.FileHandler` fuera de la capa | ✅ | 2 tests: detecta la llamada y **permite heredar** |
| CA-12 Cobertura ≥80% y batería verde | ✅ | **100%** en el módulo; 401 passed + 1 skipped; total 98% |
| CA-13 Trazabilidad | ✅ | gate-log completo |

**Resultado: 13/13 · 0 fallidos · sin rework.**

## Verificación de que las pruebas no pasan en vacío
Sustituido `FilesystemFileHandler` por `logging.FileHandler` en producción:
- **4 de 5** pruebas de rutas hostiles fallan (larga, `CON.log`, `NUL.log`, `COM1.log`).
- El test de gobernanza denuncia `src/media_optimizer/logs.py:87 -> FileHandler()`.

## Preguntas abiertas de la spec — ratificadas
- **P-1 (`logs.py` a nivel superior):** ratificada. Lo usa `ingest`, que es anterior a
  cualquier pipeline; crear `pipeline/` con un solo archivo y sin su orquestador (HU-180)
  sería estructura sin consumidor. Mismo criterio que ratificó `workspace` en HU-016.
- **P-2 (el handler crea la carpeta):** ratificada, con test.
