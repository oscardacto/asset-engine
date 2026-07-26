# Spec Técnica `HU-158` — `Contrato QualityReport en core/ (métricas, flags, veredicto)`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 91% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** el segundo contrato del dominio: `QualityReport` como dataclass
  inmutable en `core/` con los 3 conceptos del ticket — métricas, flags y veredicto.
- **Para quién:** E2 (análisis produce reportes), HU-030 (veredicto con umbrales del
  perfil), HU-035 (serialización al catálogo), HU-036/070 (ranking consume métricas).
- **Módulo / dominio:** `core/` — dominio puro, cobertura ≥95%.
- **No obvio (lo crítico que el ticket no dice de frente):** métricas y flags son
  **conjuntos abiertos** (crecen con cada HU de E2/E1) mientras el veredicto es
  **cerrado** (publicable/apoyo/descartar, literal en HU-030) ⇒ el contrato debe ser
  flexible en datos (mapping/set) y estricto en semántica (enum). Y como el KPI exige
  reproducir la auditoría manual ±2%, los valores de métrica deben ser números finitos:
  un `NaN` envenena comparaciones y rompe el determinismo — se rechaza en construcción.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- `core/quality_report.py`:
  - `Verdict` (StrEnum): `PUBLISHABLE` | `SUPPORT` | `DISCARD` (los 3 literales de HU-030).
  - `QualityReport` (`@dataclass(frozen=True, slots=True)`): `metrics: Mapping[str, float]`,
    `flags: frozenset[str]`, `verdict: Verdict`.
- Normalización en construcción: `metrics` se congela como mapping de solo lectura con
  **orden determinista** (claves ordenadas); `flags` se congela como `frozenset`.
- Invariantes fail-fast (`ValueError`): nombres de métrica no vacíos, valores **finitos**
  (sin NaN/±inf), flags no vacíos.
- API re-exportada en `core/__init__.py`; tests por CA + capa secundaria etiquetada.

### 2.2 OUT — NO entra (delimitaciones)
- Cálculo de métricas (E2: HU-020+) y detección de flags (HU-007/008/034).
- Umbrales y lógica que deciden el veredicto → HU-030 (con datos del perfil, HU-133).
- Causas del veredicto → HU-030 la extiende de forma aditiva cuando defina su semántica.
- Asociación asset↔reporte y serialización → catálogo (HU-012/035).
- Score compuesto/ranking → HU-029/070.

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | Reporte sin métricas o sin flags (asset aún no analizado del todo) | Válido: mapping/set vacíos son estados legítimos; el veredicto siempre existe | HU-030 (todo asset recibe veredicto) |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- ¿El reporte referencia a su `MediaAsset`? → P-1.
- Valores NaN/inf producidos por un cálculo defectuoso → cubierto por invariante (RN-4).

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `src/media_optimizer/core/quality_report.py` | nuevo | bajo | ✅ no existe en `develop` (e21eefd) |
| `src/media_optimizer/core/__init__.py` | modif (re-export) | bajo | ✅ leído — hoy exporta solo MediaAsset/MediaType/Orientation |
| `tests/core/test_quality_report.py` | nuevo | bajo | ✅ no existe |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| Patrón de contrato de HU-157 (frozen+slots, StrEnum, invariantes en `__post_init__`, ValueError con campo y valor) | Sí | Consistencia del dominio; mismo estilo de tests por CA |
| stdlib: `types.MappingProxyType`, `math.isfinite` | Sí | Cero dependencias nuevas |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| `QualityReport` (en memoria; persistencia = HU-035) | nuevo contrato | metrics, flags, verdict | N/A — el "esquema real" es el inventario de productores/consumidores del backlog (insumo §2) |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | Veredicto = "publicable / apoyo / descartar" | backlog HU-030 | No | `Verdict` StrEnum con exactamente esos 3 valores; requerido, no opcional |
| RN-2 | Métricas = valores numéricos comparables (paridad ±2% con auditoría) | charter §7 · backlog HU-020 | No | `Mapping[str, float]`; nombres los definen las HUs de E2 |
| RN-3 | Flags = marcas con nombre (WA, bajo-nativo, PII…) conjunto abierto | backlog HU-007/008/034 | No | `frozenset[str]` — pertenencia barata, sin orden |
| RN-4 | "Determinismo: … misma salida" | `python.md` · charter §6.1 | No | Métricas congeladas con claves ordenadas (iteración determinista); NaN/±inf rechazados en construcción |
| RN-5 | Contratos frozen, fail fast en violaciones | `python.md` | No | `frozen=True, slots=True`; `ValueError` nombrando campo y valor |
| RN-6 | Cobertura ≥95% dominio puro | CLAUDE.md Pre-Flight | No | Evidencia `pytest --cov` al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | Todo nombre de métrica no vacío (tras strip) | `ValueError` |
| V-2 | Todo valor de métrica finito (`math.isfinite`) | `ValueError` nombrando la métrica y el valor |
| V-3 | Todo flag no vacío (tras strip) | `ValueError` |
| V-4 | `metrics` de solo lectura tras construir (mutarlo lanza `TypeError`) | test lo garantiza |

---

## 6. Preguntas abiertas

### P-1 — ¿`QualityReport` referencia a su `MediaAsset` (campo `asset` o `asset_hash`)?
- **Categoría:** INFORMATIVA
- **Importa porque:** define si el reporte es autónomo o si el catálogo mantiene la asociación.
- **Va dirigida a:** @oscardacto (ratificable en el PR).
- **Mi mejor hipótesis:** no — el ticket lista 3 conceptos y "agregado al catálogo" es
  HU-035: el catálogo asocia asset↔reporte igual que asociará asset↔transformaciones.
  Añadir la referencia después es aditivo.
- **Si se asume mal, costo:** agregar un campo (aditivo, no rompe consumidores).
- **Estado:** ABIERTA

### P-2 — ¿Un reporte puede existir sin veredicto (análisis parcial)?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** no — HU-030 da veredicto a todo asset analizado; un "reporte a
  medias" no es un estado del dominio sino un intermedio interno de la etapa de análisis.
  Mantener `verdict` requerido hace el contrato total y simple.
- **Si se asume mal, costo:** `verdict: Verdict | None` después sería breaking — pero el
  flujo del pipeline (analyze produce el reporte completo) respalda la hipótesis.
- **Estado:** ABIERTA

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Reporte autónomo, sin referencia al asset (el catálogo asocia) | P-1 | Campo aditivo posterior |
| A-2 | `verdict` requerido | P-2 | Cambio de firma (breaking) — mitigado por respaldo del flujo en backlog |
| A-3 | Naming inglés + docstrings español simple (convención ratificada en PR #4 y regla de docstrings vigente) | — | N/A — ya es regla |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | HU-030 necesite "causas" y el contrato no las tenga | técnico | alta | bajo | Extensión aditiva planeada (OUT §2.2); frozen dataclass admite campo nuevo con default sin romper llamadores |
| R-2 | `Mapping` mutable pasado por el llamador y mutado después (aliasing) | técnico | media | medio | La construcción **copia** a un mapping de solo lectura — el contrato nunca comparte la referencia recibida |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (2 INFORMATIVAS)
- **Asunciones tomadas:** 3
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop e21eefd`: `core/` con MediaAsset, harness verde 17 tests)
  - [x] Productores/consumidores de los 3 conceptos cruzados en el backlog (insumo §2)
  - [x] Reglas de pureza/determinismo cruzadas (RN-4/5)
  - [x] Componentes reutilizables buscados (§3.1 — patrón HU-157 + stdlib)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 91% — el 9%: P-2 (veredicto requerido, con costo si se rompe) y R-1 (causas futuras, mitigado).

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-157 | Contrato hermano en `core/` (patrón y paquete) | DONE |
| HU-020–030, HU-035 | Producen/consumen este contrato | backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna (stdlib pura).

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — Construcción con los 3 conceptos
- **Given:** métricas `{"mean_brightness": 118.4, "sharpness": 0.72}`, flags `{"whatsapp_compressed"}`, veredicto `SUPPORT`
- **When:** se construye `QualityReport`
- **Then:** expone métricas, flags y veredicto tal como se recibieron

### CA-2 — Inmutabilidad profunda
- **Given:** un reporte construido desde un `dict` mutable
- **When:** se intenta asignar un campo, mutar `report.metrics["x"]`, o mutar el dict original del llamador
- **Then:** `FrozenInstanceError` / `TypeError` / el reporte no cambia (copió, no referenció)

### CA-3 — Invariantes fail-fast
- **Given:** métrica con valor `NaN` o `inf`, nombre de métrica vacío, o flag vacío
- **When:** se construye
- **Then:** `ValueError` inmediato nombrando el problema

### CA-4 — Veredicto cerrado
- **Then:** `Verdict` tiene exactamente `PUBLISHABLE`/`SUPPORT`/`DISCARD` y serializa a string plano

### CA-5 — Determinismo de iteración
- **Given:** las mismas métricas insertadas en órdenes distintos
- **Then:** ambos reportes son iguales y sus claves iteran en el mismo orden (ordenado)

### CA-6 — Estados vacíos legítimos
- **Given:** métricas `{}` y flags vacíos
- **Then:** el reporte se construye (con veredicto) sin error

### CA-7 — Pureza y tipado
- **Then:** `quality_report.py` importa solo stdlib; `mypy src/` estricto exit 0

### CA-8 — Cobertura dominio puro ≥95%
- **Then:** `pytest --cov=media_optimizer.core` ≥ 95%

### CA-9 — Batería completa verde
- **Then:** pytest · ruff check + format --check · mypy, todo exit 0

### CA-10 — Trazabilidad
- **Then:** gate-log con `draft`, `gate_spec`, `dev` de HU-158

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial y evaluación de gate | Claude (ejecutor) |
