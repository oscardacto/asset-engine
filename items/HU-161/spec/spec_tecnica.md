# Spec Técnica `HU-161` — `Jerarquía de excepciones del dominio (corrupto ≠ inválido ≠ bug)`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 93% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** las categorías de fallo del dominio como jerarquía de excepciones en
  `core/`, con la distinción del ticket: corrupto (se aparta, el lote sigue) ≠ inválido
  (mensaje accionable al usuario) ≠ bug (revienta sin disfraz).
- **Para quién:** HU-004/009 (corrupto→cuarentena), HU-002/011/136 (inválido→mensaje),
  y sobre todo HU-180: el orquestador decide el destino de cada fallo por su tipo.
- **Módulo / dominio:** `core/` — dominio puro, cobertura ≥95%.
- **No obvio (lo crítico que el ticket no dice de frente):** "bug" NO es una clase de la
  jerarquía — es su **ausencia**. Los bugs siguen siendo `ValueError`/`TypeError`
  estándar (como ya lanzan los contratos de `core/`) y el pipeline NO los captura: si se
  envolvieran en una excepción del dominio, el orquestador los degradaría a "asset
  fallido" y un bug real pasaría inadvertido en el resumen del lote.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- `core/errors.py`:
  - `MediaOptimizerError(Exception)` — base de todo error **esperable** del dominio.
  - `CorruptMediaError(MediaOptimizerError)` — con `source: Path` y `reason: str`
    estructurados (la cuarentena de HU-009 necesita "con causa", no solo un string).
  - `InvalidInputError(MediaOptimizerError)` — mensaje accionable; sin campos extra.
- Docstring de módulo que fija el contrato de captura: el pipeline captura
  `MediaOptimizerError`; todo lo demás pasa de largo.
- Re-export en `core/__init__.py`; tests por comportamiento + capa secundaria.

### 2.2 OUT — NO entra (delimitaciones)
- Subclases específicas (`UnsupportedFormatError`, `ProfileError`…) → nacen con
  HU-002/136 como extensión aditiva, si sus HUs las justifican.
- Cuarentena, reintentos, resumen de fallos → HU-009/180.
- Formateo de mensajes en CLI (colores, sin stacktrace) → HU-136/162.
- Códigos de error numéricos / i18n → sin consumidor en el backlog (YAGNI).

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | Bug del programa durante el procesamiento de un asset | NO capturado por el dominio: revienta con la excepción estándar | ticket ("≠ bug") + `python.md` fail fast |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- ¿Validar `reason` no vacío en el constructor? → P-1.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `src/media_optimizer/core/errors.py` | nuevo | bajo | ✅ no existe en `develop` (9f6382b) |
| `src/media_optimizer/core/__init__.py` | modif (re-export) | bajo | ✅ leído — exporta 5 nombres de 2 contratos |
| `tests/core/test_errors.py` | nuevo | bajo | ✅ no existe |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| Precedente `ValueError` en contratos (HU-157/158) | Sí — como contraste | Es la evidencia viva de que "bug" ya tiene representación estándar fuera de la jerarquía |
| stdlib `pathlib.Path` | Sí | Cero dependencias nuevas |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| N/A — excepciones, no datos persistidos | — | — | N/A |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "cuarentena **con causa**, pipeline sigue" | backlog HU-009 | No | `CorruptMediaError` lleva `source` y `reason` como campos, no solo texto |
| RN-2 | "mensajes de error accionables, nunca stacktrace" | backlog HU-136 | No | `InvalidInputError` transporta el mensaje ya accionable; el formateo es de la CLI |
| RN-3 | "un asset que falla degrada, el lote continúa" | backlog HU-180 | No | El orquestador captura `MediaOptimizerError` — una sola base para `except` |
| RN-4 | "fail fast en violaciones de contrato, fail safe en datos del usuario" | `python.md` | No | Los bugs quedan FUERA de la jerarquía: `ValueError` de los contratos no hereda de `MediaOptimizerError` |
| RN-5 | Cobertura ≥95% dominio puro | CLAUDE.md Pre-Flight | No | Evidencia `pytest --cov` al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | `except MediaOptimizerError` captura corrupto e inválido, y NO captura `ValueError` | test lo garantiza (es el contrato de HU-180) |

---

## 6. Preguntas abiertas

### P-1 — ¿`CorruptMediaError` valida que `reason` no venga vacío?
- **Categoría:** INFORMATIVA
- **Importa porque:** un reason vacío degrada la cuarentena "con causa" a "sin causa".
- **Va dirigida a:** @oscardacto (ratificable en el PR).
- **Mi mejor hipótesis:** no validar — las excepciones deben ser baratas y seguras de
  construir dentro de un `except`: un `ValueError` lanzado al construir el error
  enmascararía el fallo original con un fallo del reporte del fallo. La calidad del
  `reason` es responsabilidad del lanzador (HU-009 la testeará).
- **Si se asume mal, costo:** añadir la validación después es una línea.
- **Estado:** ABIERTA

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Constructores permisivos (sin validación interna) | P-1 | +1 línea posterior |
| A-2 | Dos categorías bastan hoy; las subclases finas llegan con sus HUs | — | Extensión aditiva |
| A-3 | Naming inglés + docstrings español simple (regla vigente) | — | N/A |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | Código futuro capture `Exception` a secas y se trague bugs | técnico | media | alto | El docstring del módulo fija el contrato de captura; HU-163 puede añadir regla ruff (`BLE001` blind-except) — anotado para esa HU |
| R-2 | Tentación de envolver bugs en `MediaOptimizerError` "para que el lote no se caiga" | técnico | media | alto | Documentado en el propio módulo y en esta spec §1: degradar bugs los esconde del resumen de fallos |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 1 total — **0 bloqueantes** (1 INFORMATIVA)
- **Asunciones tomadas:** 3
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop 9f6382b`: `core/` con 2 contratos, 31 tests verdes)
  - [x] Lanzadores/capturadores por categoría cruzados en el backlog (insumo §2)
  - [x] Precedente de bugs-como-ValueError verificado en `media_asset.py`/`quality_report.py`
  - [x] Componentes reutilizables buscados (§3.1)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 93% — el 7%: P-1 (permisividad del constructor) y R-1 (disciplina de captura futura).

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-150 | Consume el esqueleto | DONE |
| HU-004/009 · HU-002/011/136 · HU-180 | Lanzan/capturan estas excepciones | backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna (stdlib pura).

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — Jerarquía correcta
- **Then:** `CorruptMediaError` e `InvalidInputError` heredan de `MediaOptimizerError`, que hereda de `Exception` (no de `BaseException` directo)

### CA-2 — El contrato de captura del orquestador
- **Given:** un bloque `except MediaOptimizerError`
- **When:** dentro se lanza `CorruptMediaError`, `InvalidInputError` o `ValueError`
- **Then:** captura las dos primeras; el `ValueError` (bug) pasa de largo

### CA-3 — Corrupto lleva su causa estructurada
- **Given:** `CorruptMediaError(source=Path("originales/x.jpg"), reason="JPEG truncado")`
- **Then:** expone `source` y `reason` como campos, y `str(e)` incluye ambos

### CA-4 — Inválido transporta el mensaje accionable
- **Given:** `InvalidInputError("el perfil no declara 'ambientes': añade la clave o usa el perfil de ejemplo")`
- **Then:** `str(e)` devuelve exactamente ese mensaje

### CA-5 — Pureza y tipado
- **Then:** `errors.py` importa solo stdlib; `mypy src/` estricto exit 0

### CA-6 — Cobertura ≥95% en `core/`
- **Then:** `pytest --cov=media_optimizer.core` ≥ 95%

### CA-7 — Batería completa verde
- **Then:** pytest · ruff check + format --check · mypy, todo exit 0

### CA-8 — Trazabilidad
- **Then:** gate-log con `draft`, `gate_spec`, `dev` de HU-161

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial y evaluación de gate | Claude (ejecutor) |
| 2026-07-26 | DEV: implementado según §2.1 sin desviaciones (A-1/A-2/A-3 aplicadas); batería 40 tests verde, core/ 100% | Claude (ejecutor) |
