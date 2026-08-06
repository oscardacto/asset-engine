# Spec Técnica `HU-013` — `Re-ingesta idempotente: mismo input no duplica ni reprocesa`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 90% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** que volver a ingerir la misma carpeta no duplique assets ni repita
  trabajo ya hecho.
- **Para quién:** HU-017 (CLI `ingest`), HU-019 (etiquetas manuales que sobreviven),
  HU-182 (reanudación de runs).
- **Módulo / dominio:** `media_optimizer.ingest` — módulo nuevo `reingest.py`.
- **No obvio:** "idempotente" esconde **dos exigencias distintas** que el ticket junta en
  una frase. *No duplicar* es cuestión de identidad —resuelta por ADR-004: el hash manda—.
  *No reprocesar* exige saber **qué cambió** entre dos estados del mismo lote, y ahí
  aparece un caso que ninguna de las dos frases nombra: **un archivo que se renombró o se
  movió de carpeta**. Por contenido es el mismo asset; por ruta parece uno nuevo más uno
  desaparecido. Tratarlo como tal duplicaría el trabajo y perdería lo que el usuario haya
  anotado sobre él.

---

## 2. Alcance

### 2.1 IN
- `ingest/reingest.py`:
  - `AssetChange` (StrEnum): `NEW`, `UNCHANGED`, `MOVED`, `REMOVED`.
  - `ReingestPlan` (frozen): las cuatro colecciones, más `has_changes`.
  - `plan_reingest(previous: Catalog, current: Catalog) -> ReingestPlan`.
- **Comparación por contenido**, no por ruta (ADR-004 §1).
- Detección explícita de **movidos/renombrados**: mismo hash, distinta ruta.
- Orden determinista en las cuatro colecciones.
- Tests contra los CA + capa secundaria.

### 2.2 OUT
- Ejecutar el plan (saltarse etapas, reutilizar resultados) → HU-180/HU-182.
- Sidecar de etiquetas manuales → HU-019 (consumirá `MOVED` para no perderlas).
- CLI y resumen en consola → HU-017.
- Comparar *contenido de análisis* (métricas, veredictos) → E2; aquí solo la identidad.
- Near-duplicates perceptuales → HU-075.

### 2.3 Casos límite
| # | Caso | Tratamiento | Fuente |
|---|---|---|---|
| 1 | Mismo contenido, ruta distinta | `MOVED`, no `NEW` + `REMOVED` | ADR-004 §1 |
| 2 | Dos copias del mismo contenido en el lote | Un solo asset; el lote real ya trae 15 grupos así | medición del lote |
| 3 | Lote sin cambios | Las cuatro colecciones reflejan solo `UNCHANGED`; `has_changes` falso | ticket |

### 2.4 No mencionados → §6
- ¿Qué hacer si un hash aparece en varias rutas nuevas? → P-1.

---

## 3. Componentes

| Componente | Cambio | Verificado |
|---|---|---|
| `ingest/reingest.py` | nuevo | ✅ no existe en `develop` (1c9b2e0) |
| `ingest/__init__.py` | re-export | ✅ leído |
| `tests/ingest/test_reingest.py` | nuevo | ✅ no existe |

### 3.1 Reutilizables
| Componente | ¿Reutilizar? | Justificación |
|---|---|---|
| `Catalog` / `CatalogEntry` (HU-012) | Sí | Las dos entradas de la comparación; ya traen hash y ruta relativa |
| Identidad por contenido (ADR-004) | Sí | Decisión ya tomada, no se re-litiga |
| Patrón frozen + StrEnum de `core/` | Sí (estilo) | Consistencia |

**Esta HU no toca disco**: compara dos catálogos ya cargados. Por eso no aparece en el
inventario de accesos al filesystem.

---

## 4. Modelo de datos
`ReingestPlan` y `AssetChange` en memoria. Sin persistencia (el plan se recalcula; guardarlo
sería estado derivado duplicado).

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|---|---|---|
| RN-1 | "El identificador de un asset es el hash de su contenido" | ADR-004 §1 | La comparación es por hash; la ruta solo distingue `MOVED` de `UNCHANGED` |
| RN-2 | "mismo input no duplica ni reprocesa" | ticket | `NEW` solo para hashes ausentes del catálogo previo |
| RN-3 | "sobrevive re-ingestas" (etiquetas manuales) | backlog HU-019 | `MOVED` debe distinguirse: si se tratara como `NEW`+`REMOVED`, HU-019 perdería las anotaciones |
| RN-4 | Determinismo | charter §6.1 | Colecciones ordenadas; mismo par de catálogos ⇒ mismo plan |
| RN-5 | Cobertura ≥80% | Pre-Flight | Evidencia al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | Un renombrado produce `MOVED`, nunca `NEW`+`REMOVED` | test |
| V-2 | Comparar un catálogo consigo mismo no produce cambios | test |
| V-3 | Cada asset del catálogo actual aparece exactamente en una categoría | test (particiones disjuntas) |

---

## 6. Preguntas abiertas

### P-1 — ¿Y si el mismo contenido aparece en varias rutas nuevas?
- **Categoría:** INFORMATIVA
- **Importa porque:** el lote real trae 15 grupos de duplicados; es un caso que ocurre.
- **Mi mejor hipótesis:** el asset es uno solo (identidad por contenido) y se reporta como
  `UNCHANGED` o `MOVED` según si alguna de sus rutas coincide con la previa. Las rutas
  adicionales son copias del mismo asset, y el catálogo ya las lista por separado; la
  política de cuál conservar es de HU-018.
- **Costo si se asume mal:** cambiar cómo se agrupa, sin tocar la comparación.
- **Estado:** ABIERTA

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|---|---|
| A-1 | La identidad es el hash; la ruta solo clasifica | Contradiría ADR-004 |
| A-2 | El plan no se persiste: se recalcula | Añadir serialización (aditivo) |
| A-3 | `MOVED` se decide por "mismo hash, ninguna ruta en común" | Ajustar el criterio de agrupación |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| R-1 | Tratar un renombrado como alta+baja y perder las etiquetas de HU-019 | media | **alto** | `MOVED` es una categoría propia y hay test específico |
| R-2 | Comparar por ruta "porque es más simple" en algún consumidor | media | alto | La API no expone comparación por ruta; solo el plan ya calculado |

---

## 9. Confianza global

- **Preguntas abiertas:** 1 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] Codebase leído (`develop 1c9b2e0`, 260 tests verdes; `Catalog` disponible)
  - [x] Consumidores cruzados (HU-017/019/182) con su fila literal
  - [x] Identidad por contenido verificada en ADR-004 §1 — no se re-decide
  - [x] **Medición del lote real**: 109 archivos, 86 únicos, 15 grupos de duplicados ⇒ el
        caso de contenido repetido en varias rutas no es hipotético
  - [x] Reutilizables verificados en código
- **Recomendación:** ✅ **LISTA PARA DEV** (0 bloqueantes · ≥85%)
- **Confianza: 90%.** El 10%: P-1 (agrupación cuando un hash tiene varias rutas) y R-1.

---

## 10. Dependencias
| ID | Relación | Estado |
|---|---|---|
| HU-012 | Aporta `Catalog` | DONE |
| ADR-004 | Fija la identidad | Aceptado |
| HU-017, HU-019, HU-182 | Consumidores | backlog |

---

## 11. Criterios de aceptación

- **CA-1** — Comparar un catálogo consigo mismo: todo `UNCHANGED`, `has_changes` falso.
- **CA-2** — Un archivo nuevo aparece como `NEW`.
- **CA-3** — Un archivo que ya no está aparece como `REMOVED`.
- **CA-4** — Un archivo renombrado o movido aparece como `MOVED`, **nunca** como `NEW`+`REMOVED`.
- **CA-5** — Un archivo cuyo contenido cambió (mismo nombre, otro hash) es `NEW` + `REMOVED`: es otro asset.
- **CA-6** — Las cuatro colecciones son disjuntas y cubren todo.
- **CA-7** — Determinismo: el mismo par de catálogos produce el mismo plan.
- **CA-8** — Primera ingesta (catálogo previo vacío): todo `NEW`.
- **CA-9** — Cobertura ≥80% y batería verde.
- **CA-10** — Trazabilidad en el gate-log.

---

## 12. Historial de cambios
| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación; separa las dos exigencias que el ticket junta y nombra el caso del renombrado | Claude (ejecutor) |
