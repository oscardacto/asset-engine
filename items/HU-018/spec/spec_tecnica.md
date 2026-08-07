# Spec Técnica `HU-018` — `Reporte inventory (report inventory)`

> **Estado:** LISTA PARA DEV
> **Fecha:** 2026-08-06
> **Confianza global:** 90%

## 1. Resumen ejecutivo
- **Qué se pide:** `report inventory` — una tabla por asset (dimensiones, orientación,
  flags) más la cuarentena con causas, en texto o Markdown, escrita en `reports/` del
  workspace y mostrada en consola.
- **Módulo:** `pipeline/reports.py` — los generadores de reporte, simétrico a `stages.py`.
- **No obvio:** el reporte es **una salida persistida**, así que cae bajo la promesa de
  determinismo byte a byte (charter §6.1): mismo catálogo ⇒ mismo archivo. Por eso lo
  genera código propio sobre datos ya ordenados del catálogo, sin timestamps.

## 2. Alcance
### 2.1 IN
- `pipeline/reports.py`: `available_reports()`, `generate_report(name, request)` →
  contenido + ruta escrita. Generador de `inventory`: tabla por asset + cuarentena.
- Formatos `texto` y `markdown` (mismo contenido, distinta tabla). `jsonl` queda declarado
  en el enum del comando pero es de HU-183: pedirlo para `inventory` avisa con claridad.
- `ReportEntry.available` derivado del generador (mismo patrón que las etapas).
- `cli/commands/report.py` invoca la generación real.
### 2.2 OUT
- Flags de calidad (WhatsApp, bajo nativo, PII) → HU-007/008/034, aditivo sobre la columna
  de flags que la tabla ya trae.
- Reportes `analysis`/`develop`/`selection`/`reel`/`run`/`history` → sus HUs.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Sin catálogo en el workspace | `InvalidInputError` con "ejecuta primero run ingest" (ya existe) |
| 2 | Catálogo vacío | Reporte válido que dice 0 assets |
| 3 | Formato `jsonl` para inventory | Mensaje claro: ese formato es del reporte `run` (HU-183) |
| 4 | Nombre de archivo hostil en el catálogo | La tabla lo muestra tal cual; el archivo del reporte se escribe con nombre fijo |

## 5. Reglas de negocio
| # | Regla | Implicación |
|---|-------|-------------|
| RN-1 | Salida persistida determinista (charter §6.1) | Sin timestamps; datos ya ordenados; test byte a byte |
| RN-2 | `report` no calcula (arquitectura) | Solo lee el catálogo y formatea |
| RN-3 | Todo IO por la capa (ADR-004) | Lectura y escritura vía `filesystem` |
| RN-4 | Formato Maestro §8.2 | Una fila por asset: archivo, dims, orientación, flags |

## 8. Riesgos
| # | Riesgo | Mitigación |
|---|--------|------------|
| R-1 | El reporte gane un timestamp y rompa el determinismo | Test: dos generaciones ⇒ mismos bytes |
| R-2 | `available` del reporte y el generador diverjan | Derivado, como en etapas; test |

## 9. Confianza global
- 0 bloqueantes · piezas verificadas en código (catálogo, workspace, comando). **90%** ✅

## 11. Criterios de aceptación
- **CA-1** — `report inventory` escribe `reports/inventory.md` (o `.txt`) y lo muestra en consola.
- **CA-2** — Una fila por asset: archivo, ancho×alto, orientación, flags.
- **CA-3** — La cuarentena aparece con su causa.
- **CA-4** — Dos generaciones sobre el mismo catálogo ⇒ **mismos bytes**.
- **CA-5** — Sin catálogo ⇒ código 3 con mensaje accionable; catálogo vacío ⇒ reporte válido.
- **CA-6** — La disponibilidad se deriva del generador.
- **CA-7** — Gobernanza verde; cobertura ≥80%; batería verde; gate-log.
