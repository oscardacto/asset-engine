# Spec Técnica `HU-168` — `Contrato StageReport`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-08-06
> **Confianza global:** 90% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** la ficha que cada etapa del pipeline entrega al terminar: tiempo,
  memoria pico, transformaciones aplicadas y scores.
- **Para quién:** HU-180 (orquestador), HU-183 (métricas JSONL), HU-165 (benchmarks),
  HU-181 (reporte consolidado).
- **Módulo:** `media_optimizer.core.stage_report` — dominio puro, sin IO.
- **No obvio — el contrato contiene su propia contradicción.** CLAUDE.md exige que toda
  etapa reporte **tiempo y memoria pico**; el charter §6.1 promete que la misma entrada
  produce **la misma salida byte a byte**, verificado con golden tests. Medir la misma
  etapa dos veces da números distintos. Si un `StageReport` completo llegara a un golden
  test o a un manifiesto comparado por hash, **la suite fallaría de forma intermitente y la
  causa sería invisible**: el diff diría `0.031` vs `0.029` y parecería ruido, no un error
  de diseño. El contrato tiene que hacer imposible esa mezcla, no solo desaconsejarla.

---

## 2. Alcance

### 2.1 IN
- `StageReport` (frozen): `stage`, `duration_seconds`, `peak_memory_bytes`,
  `transforms` (reutiliza `TransformHistory` de HU-159), `scores`.
- **La separación entre lo medido y lo reproducible**, explícita en la API:
  `reproducible_part()` devuelve solo lo que un golden test puede comparar.
- Invariantes: nombre de etapa no vacío, tiempo y memoria ≥ 0, scores finitos.

### 2.2 OUT
- **Medir** el tiempo y la memoria → es impuro y va en `pipeline/`, con HU-180. `core/` no
  llama a `perf_counter` ni a `tracemalloc`.
- **Serializar a JSONL** → HU-183.
- **Conteos del run** (assets procesados, fallidos) → HU-183 los define a nivel de run;
  este contrato es por etapa y su enunciado son cuatro campos, no cinco.
- **Presupuestos de rendimiento** (cuánto *debería* tardar) → HU-165.
- **Renderizar a Markdown** → HU-181.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Etapa que no aplica transformaciones (análisis puro) | Historial vacío; válido |
| 2 | Etapa que no produce scores | Mapping vacío; válido |
| 3 | Duración de 0.0 | Válida — una etapa puede ser más rápida que la resolución del reloj |
| 4 | Duración o memoria negativa | `ValueError` — no es un dato pobre, es un dato imposible |
| 5 | Dos reportes de la misma etapa con tiempos distintos | Sus partes reproducibles son **iguales**; es la propiedad que define el diseño |

---

## 3. Componentes

| Componente | Cambio | Verificado |
|---|---|---|
| `src/media_optimizer/core/stage_report.py` | nuevo | ✅ no existe en `develop` |
| `src/media_optimizer/core/__init__.py` | exporta `StageReport` y `ReproducibleStageSummary` | ✅ leído |
| `tests/core/test_stage_report.py` | nuevo | ✅ no existe |

### 3.1 Reutilizables
| Componente | ¿Reutilizar? | Justificación |
|---|---|---|
| `TransformHistory` (HU-159) | **Sí, obligatorio** | Ya es la secuencia inmutable y ordenada de retoques. Duplicarla sería tener dos versiones de la evidencia de auditoría |
| Patrón de mapping validado de `QualityReport` | Sí | Los scores son el mismo problema: ordenado, inmutable, finito |
| Estilo de `__post_init__` de `MediaAsset` | Sí | `ValueError` con el valor recibido |

---

## 4. Modelo de datos

```
StageReport                            ← lo que la etapa entrega
├── stage: str                           qué etapa fue
├── duration_seconds: float   ⏱ MEDIDO   irreproducible
├── peak_memory_bytes: int    ⏱ MEDIDO   irreproducible
├── transforms: TransformHistory         reproducible
└── scores: Mapping[str, float]          reproducible

    .reproducible_part() ──▶ ReproducibleStageSummary(stage, transforms, scores)
```

**La regla que impone el tipo:** lo que se compara en un golden test o se hashea en un
manifiesto es `ReproducibleStageSummary`, que es un **tipo distinto**. Un `StageReport`
completo no puede colarse ahí por descuido: no encaja. La disciplina la sostiene el
verificador de tipos, no la memoria de quien escribe el test.

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|-------|--------|-------------|
| RN-1 | Toda etapa reporta tiempo, memoria pico, transformaciones y scores | CLAUDE.md | Los cuatro campos son obligatorios, no opcionales |
| RN-2 | Misma entrada ⇒ misma salida byte a byte | charter §6.1 | La parte comparable se separa en un tipo propio |
| RN-3 | `core/` sin IO ni impureza | CLAUDE.md | Este módulo no mide: recibe lo medido |
| RN-4 | Fail fast en violación de contrato | `python.md` | `ValueError` al construir |
| RN-5 | Cobertura ≥95% en dominio puro | Pre-Flight | Evidencia al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|-----------|----------|
| V-1 | Nombre de etapa no vacío | `ValueError` |
| V-2 | `duration_seconds` finito y ≥ 0 | `ValueError` |
| V-3 | `peak_memory_bytes` ≥ 0 | `ValueError` |
| V-4 | Scores finitos con nombre no vacío | `ValueError` |
| V-5 | Dos reportes que solo difieren en tiempo/memoria tienen la misma parte reproducible | test |

---

## 6. Preguntas abiertas

### P-1 — ¿La memoria pico en bytes o en MiB?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** **bytes**, entero. Es lo que devuelven `tracemalloc` y el sistema
  operativo; convertir a MiB en el contrato metería un float y un redondeo entre la medida y
  el dato. Presentarlo legible es tarea de quien lo muestra (HU-181).
- **Estado:** ABIERTA

### P-2 — ¿`reproducible_part()` debería incluir la duración redondeada?
- **Categoría:** IMPORTANTE (no bloqueante)
- **Mi mejor hipótesis:** **no**. Redondear no vuelve determinista un tiempo, solo hace que
  la intermitencia sea **más rara y por tanto más difícil de diagnosticar**: el golden test
  pasaría 99 de cada 100 veces y el fallo centésimo parecería un fantasma. Un dato es
  reproducible o no lo es; no hay término medio útil aquí. Comparar rendimiento contra un
  presupuesto es HU-165, y ese es un test distinto con tolerancia explícita.
- **Costo si se asume mal:** añadir un campo a un dataclass.
- **Estado:** ABIERTA

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|----------|-------------------|
| A-1 | Memoria en bytes enteros (P-1) | Conversión en la capa de presentación |
| A-2 | La parte reproducible excluye todo tiempo (P-2) | Añadir un campo |
| A-3 | Los cuatro campos del mandato bastan; los conteos son de run (HU-183) | Aditivo |
| A-4 | `TransformHistory` sirve tal cual para etapas que no transforman (historial vacío) | Ninguno: ya tiene default `()` |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R-1 | Un tiempo medido acaba en un golden test y lo vuelve intermitente | **alta** si no se separa | **alto** (falla rara, diagnóstico caro) | `reproducible_part()` como tipo distinto + test que lo demuestra con dos reportes de tiempos distintos |
| R-2 | Alguien mida dentro de `core/` para "completar" el contrato | media | medio | El test de arquitectura ya prohíbe IO en `core/`; el docstring dice quién mide y dónde |
| R-3 | El contrato se quede corto para HU-183 | baja | bajo | Los conteos son de run, no de etapa; añadirlos es aditivo |

---

## 9. Confianza global

- **Preguntas abiertas:** 2 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] Mandato de observabilidad leído literal en CLAUDE.md — son cuatro campos
  - [x] `TransformHistory` leído en código: `steps` con default `()`, reutilizable tal cual
  - [x] Patrón de validación de mappings verificado en `QualityReport`, no supuesto
  - [x] Los 4 consumidores revisados en el backlog
  - [x] Tensión determinismo/observabilidad confirmada contra charter §6.1 y §7
- **Recomendación:** ✅ **LISTA PARA DEV**
- **Confianza: 90%.** El 10% es P-2 y R-3: son decisiones aditivas y baratas de revertir.

---

## 10. Dependencias
| ID | Relación | Estado |
|----|----------|--------|
| HU-150, HU-159 | Esqueleto y `TransformHistory` | DONE |
| HU-180, HU-183, HU-165, HU-181 | Lo consumirán | backlog |

---

## 11. Criterios de aceptación

- **CA-1** — `StageReport` es inmutable y expone los cuatro campos del mandato.
- **CA-2** — `reproducible_part()` devuelve un tipo distinto que **no** contiene tiempo ni memoria.
- **CA-3** — Dos reportes de la misma etapa con tiempo y memoria distintos tienen partes reproducibles **iguales**.
- **CA-4** — Duración o memoria negativas levantan `ValueError`; `0.0` y `0` son válidos.
- **CA-5** — Score no finito o sin nombre levanta `ValueError`.
- **CA-6** — Nombre de etapa vacío levanta `ValueError`.
- **CA-7** — Los scores iteran en orden estable y son de solo lectura.
- **CA-8** — Una etapa sin transformaciones y sin scores produce un reporte válido.
- **CA-9** — `core/` sigue sin IO: el test de gobernanza pasa.
- **CA-10** — Cobertura ≥95% en el módulo y batería verde.
- **CA-11** — Trazabilidad en el gate-log.

---

## 12. Historial de cambios
| Fecha | Cambio | Por |
|-------|--------|-----|
| 2026-08-06 | Creación | Claude (ejecutor) |
