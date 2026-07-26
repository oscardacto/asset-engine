# Spec Técnica `HU-159` — `Contrato Transform + historial de transformaciones aplicadas`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 92% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** los 2 conceptos del ticket como contratos en `core/`: `Transform`
  (qué operación, con qué parámetros) y el historial ordenado de transformaciones
  aplicadas a un asset.
- **Para quién:** E3 completo (cada etapa del revelado es un transform), HU-056
  (pipeline componible declarado en el perfil), HU-057 (sidecar auditable), HU-168
  (StageReport) y el charter §6.3 (la no-destructividad exige historial).
- **Módulo / dominio:** `core/` — dominio puro, cobertura ≥95%.
- **No obvio (lo crítico que el ticket no dice de frente):** el transform NO ejecuta
  nada — es el **registro declarativo** (nombre + parámetros como datos del perfil,
  HU-056). Y el historial es **posicional**: su orden es el orden de aplicación (CLAHE
  antes de saturación ≠ después), así que a diferencia de las métricas de HU-158, los
  pasos jamás se reordenan — pero los parámetros de cada paso sí se congelan con claves
  ordenadas para el determinismo de serialización.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- `core/transform.py`:
  - `ParamValue` (alias): `float | int | str | bool` — escalares serializables a JSON.
  - `Transform` (`frozen`, `slots`): `name: str` + `params: Mapping[str, ParamValue]`
    congelado como mapping de solo lectura con claves ordenadas (copia defensiva).
  - `TransformHistory` (`frozen`, `slots`): `steps: tuple[Transform, ...]` (vacío por
    defecto) + `append()` **puro** que devuelve un historial nuevo + `__len__`/`__iter__`.
- Invariantes fail-fast (`ValueError`): nombre de transform no vacío, nombres de
  parámetro no vacíos, floats finitos (regla anti-NaN de HU-158).
- Re-export en `core/__init__.py`; tests por comportamiento + capa secundaria.

### 2.2 OUT — NO entra (delimitaciones)
- Ejecución real de transforms sobre píxeles → E3 (HU-050+).
- Registro/despacho nombre→implementación → HU-056 (pipeline componible).
- Serialización del sidecar a disco → HU-057 (con el ADR de catálogo HU-153).
- Validación de que un nombre de transform "exista" → HU-056 (aquí el conjunto es abierto).
- Tiempos/memoria por etapa → HU-168 (`StageReport`).

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | Asset sin transformar (historial vacío) | Estado legítimo y default — un original ingerido aún no tiene pasos | charter §6.3 (el historial nace con la primera salida) |
| 2 | El mismo transform aplicado dos veces (p. ej. resize doble) | Legítimo: el historial es secuencia, no conjunto — se registran ambos | HU-056 (el perfil declara el orden) |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- ¿Nombres de transform como enum cerrado? → P-1.
- ¿Parámetros anidados (listas/dicts)? → P-2.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `src/media_optimizer/core/transform.py` | nuevo | bajo | ✅ no existe en `develop` (8843621) |
| `src/media_optimizer/core/__init__.py` | modif (re-export) | bajo | ✅ leído — 8 nombres públicos |
| `tests/core/test_transform.py` | nuevo | bajo | ✅ no existe |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| Patrón mapping-congelado-con-copia-defensiva de `QualityReport` | Sí | Mismo problema (params del llamador), misma solución, misma semántica de hash (`field(hash=False)`) |
| Regla anti-NaN de HU-158 | Sí | Un `clip_limit=NaN` rompería el replay determinista igual que una métrica NaN |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| `Transform` / `TransformHistory` (en memoria; sidecar = HU-057) | nuevos contratos | name, params, steps | N/A — el "esquema real" es el inventario de consumidores del backlog (insumo §2) |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "orden y parámetros de transforms **declarados en el perfil**" | backlog HU-056 | No | El contrato es declarativo: nombre + params como datos; cero lógica de píxeles |
| RN-2 | "historial de transformaciones **aplicadas**" · "sidecar **auditable**" | ticket · HU-057 · charter §6.3 | No | Secuencia ordenada e inmutable; `append` puro (el historial previo nunca muta — auditable) |
| RN-3 | Determinismo (misma entrada+perfil ⇒ misma salida) | charter §6.1 | No | Params con claves ordenadas y floats finitos; steps en orden de aplicación estricto |
| RN-4 | Contratos frozen, fail fast; ValueError = bug | `python.md` · precedente HU-157/158/161 | No | Mismo estilo: `frozen=True, slots=True`, mensajes nombrando campo y valor |
| RN-5 | Cobertura ≥95% dominio puro | CLAUDE.md Pre-Flight | No | Evidencia `pytest --cov` al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | `name` no vacío (tras strip) | `ValueError` |
| V-2 | Todo nombre de parámetro no vacío | `ValueError` |
| V-3 | Todo parámetro `float` finito (`bool`/`int`/`str` exentos) | `ValueError` nombrando parámetro y valor |
| V-4 | `append` no muta el historial original | test lo garantiza |

---

## 6. Preguntas abiertas

### P-1 — ¿Los nombres de transform son un enum cerrado?
- **Categoría:** INFORMATIVA
- **Importa porque:** un enum daría autocompletado y typos imposibles, pero acoplaría `core/` a E3.
- **Va dirigida a:** @oscardacto (ratificable en el PR).
- **Mi mejor hipótesis:** no — el conjunto es abierto (cada HU de E3 aporta el suyo y el
  perfil los referencia **por nombre como dato**, HU-056); un enum en `core/` habría que
  tocarlo en cada HU de revelado, exactamente el churn que evitamos en las métricas de HU-158.
  La validación nombre→implementación pertenece al despachador (HU-056).
- **Si se asume mal, costo:** introducir el enum después es mecánico (los strings ya existirían).
- **Estado:** ABIERTA

### P-2 — ¿Se admiten parámetros anidados (listas, dicts)?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** no — los consumidores conocidos usan escalares (clip limit,
  tiles, targets, ángulo); lo compuesto se aplana (`tiles_x`/`tiles_y`). Escalares planos
  mantienen trivial la serialización del sidecar y la igualdad por valor.
- **Si se asume mal, costo:** ampliar `ParamValue` después es aditivo.
- **Estado:** ABIERTA

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Nombres de transform como `str` libre no vacío | P-1 | Enum aditivo posterior |
| A-2 | `ParamValue = float \| int \| str \| bool` (escalares planos) | P-2 | Ampliación aditiva |
| A-3 | Historial como contrato propio (no `tuple` pelada): `append` puro + iteración le dan semántica de auditoría | — | Degradar a alias es trivial si sobrara |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | HU-057 necesite metadatos por paso (timestamp, duración) que el contrato no tiene | técnico | media | bajo | Timestamps/duración son observabilidad ⇒ pertenecen a `StageReport` (HU-168), no al transform declarativo; si HU-057 los quiere en el sidecar, los tomará de ambos contratos |
| R-2 | `bool` es subclase de `int` en Python y confunda la validación de floats | técnico | baja | bajo | La validación solo aplica `isfinite` a `float` reales; test de capa secundaria lo cubre |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (2 INFORMATIVAS)
- **Asunciones tomadas:** 3
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop 8843621`: `core/` con 3 módulos, 40 tests verdes)
  - [x] Productores/consumidores cruzados en el backlog (insumo §2 — E3, HU-056/057/168)
  - [x] Patrón reutilizable identificado y no asumido (§3.1 — mapping congelado de HU-158)
  - [x] Reglas de determinismo cruzadas (RN-3)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 92% — el 8%: P-1 (enum vs string libre) y R-1 (metadatos del sidecar).

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-157 | Contrato hermano (patrón y paquete) | DONE |
| HU-050–057 (E3), HU-168 | Producen/consumen estos contratos | backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna (stdlib pura).

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — Transform declarativo
- **Given:** `Transform("clahe", {"clip_limit": 2.0, "tiles_x": 8, "tiles_y": 8})`
- **Then:** expone `name` y `params` tal como se recibieron

### CA-2 — Inmutabilidad profunda
- **When:** se asigna un campo, se muta `params["x"]`, o se muta el dict original del llamador
- **Then:** `FrozenInstanceError` / `TypeError` / el transform no cambia

### CA-3 — Invariantes fail-fast
- **Given:** nombre vacío, nombre de parámetro vacío, o `clip_limit=NaN`
- **Then:** `ValueError` inmediato nombrando el problema

### CA-4 — Historial auditable
- **Given:** un historial vacío (default)
- **When:** `append(t1)` y luego `append(t2)`
- **Then:** cada `append` devuelve un historial NUEVO (el anterior queda intacto), con los pasos en orden de aplicación

### CA-5 — Igualdad por valor
- **Then:** transforms con mismo nombre+params son iguales; historiales con mismos pasos en el mismo orden son iguales; distinto orden ⇒ distintos

### CA-6 — Params deterministas, pasos posicionales
- **Given:** los mismos params insertados en órdenes distintos
- **Then:** los transforms son iguales y sus claves iteran ordenadas — pero los `steps` del historial conservan el orden de aplicación, jamás se reordenan

### CA-7 — Pureza y tipado
- **Then:** `transform.py` importa solo stdlib; `mypy src/` estricto exit 0

### CA-8 — Cobertura ≥95% en `core/`
- **Then:** `pytest --cov=media_optimizer.core` ≥ 95%

### CA-9 — Batería completa verde
- **Then:** pytest · ruff check + format --check · mypy, todo exit 0

### CA-10 — Trazabilidad
- **Then:** gate-log con `draft`, `gate_spec`, `dev` de HU-159

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial y evaluación de gate | Claude (ejecutor) |
| 2026-07-26 | DEV: implementado según §2.1 sin desviaciones (A-1/A-2/A-3 aplicadas); batería 57 tests verde, core/ 100% | Claude (ejecutor) |
