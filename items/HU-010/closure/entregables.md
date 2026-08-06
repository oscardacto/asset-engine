# Entregables — HU-010

## Integración
| Merge | Rama | Descripción |
|-------|------|-------------|
| `acc6e3d` | `feature/HU-010-nombres-hostiles` → `develop` | Capa de acceso al filesystem + migración de 12 puntos + ADR-004. Batería verificada sobre la rama fusionada |

## Evidencia contra los criterios de aceptación (spec §11)

| CA | Resultado | Evidencia |
|----|-----------|-----------|
| CA-1 `CON.jpg` no bloquea | ✅ | `test_un_nombre_de_dispositivo_no_bloquea_el_proceso` — subproceso con timeout de 15 s, retorna con el tamaño correcto |
| CA-2 Nombres antes inaccesibles se procesan | ✅ | parametrizado sobre `punto.jpg.`, `espacio.jpg `, `COM1.jpg`, `NUL.jpg` |
| CA-3 Ruta >260 aparece en el escaneo | ✅ | `test_una_ruta_larguisima_ya_no_desaparece_del_escaneo` (ruta de 368 caracteres) |
| CA-4 Los 15 tests de HU-001 pasan sin modificación | ✅ | suite completa verde, `test_scanner.py` intacto |
| CA-5 Orden estable con nombres hostiles | ✅ | `test_el_orden_sigue_siendo_estable_con_nombres_hostiles` |
| CA-6 Invariantes de la capa (F-1, F-2) | ✅ | `TestTraduccionDeRutas` (idempotencia, sin prefijo a la salida) |
| CA-7 El test de cumplimiento detecta evasiones | ✅ | detectó los 12 en línea base y 6 falsos positivos al afinar el receptor |
| CA-8 POSIX: capa identidad | ⚠️ **parcial** | test presente pero `skipped` en Windows; **sin verificar en Linux real** |
| CA-9 No destructivo | ✅ | heredado de los tests de HU-001/009, suite verde |
| CA-10 Cobertura ≥80% y batería | ✅ | `ingest/` **98%**, 217 passed + 1 skipped, ruff y mypy limpios |
| CA-11 Trazabilidad | ✅ | gate-log con draft/gate_spec/dev + qa/done |

**Resultado: 10/11 plenos, 1 parcial (CA-8, declarado, no oculto).**

## Validación sobre datos reales
Sobre el lote del cliente, antes y después de la migración:

| Métrica | Antes | Después |
|---|---|---|
| Archivos encontrados | 107 | **109** |
| Aceptados | 100 | **102** |
| Assets únicos por contenido | 85 | **86** |

**Se recuperaron 2 archivos que el escaneo perdía en silencio.** El invariante I-2 de ADR-004
no era una preocupación teórica.

## Commits relevantes
- `1b217c8` — DRAFT+SPEC + ADR-004 (hipótesis de "nombres hostiles" refutada por evidencia)
- `74e03c4` — inventario de superficie de impacto + regla en `python.md`
- `7ed2408` — DEV: capa, migración de los 12 puntos, regresión, backlog alineado
- `acc6e3d` — merge a `develop`
