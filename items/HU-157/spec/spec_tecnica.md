# Spec Técnica `HU-157` — `Contrato MediaAsset en core/ (foto/video, dimensiones, hash, origen)`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 92% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** el primer contrato del dominio: `MediaAsset` como dataclass inmutable
  en `core/`, cubriendo exactamente los 4 conceptos del ticket — tipo (foto/video),
  dimensiones, hash de contenido y origen.
- **Para quién:** HU-158/159 (contratos que componen), HU-001/005/006/012 (ingesta y
  catálogo) — es el sustantivo central de todo el pipeline.
- **Módulo / dominio:** `core/` — dominio puro, **sin IO**, cobertura exigida ≥95%.
- **No obvio (lo crítico que el ticket no dice de frente):** `origen` es un **valor**
  (`pathlib.Path`), no un recurso: el contrato jamás abre el archivo — validar que el
  path exista sería IO y rompería la pureza de `core/`; esa verificación pertenece a la
  ingesta (E1). Y la orientación V/H que audita el Maestro §8.2 es propiedad derivada
  **pura** de las dimensiones, así que nace aquí (la parte EXIF de HU-005 queda en E1).

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- Paquete `core/` (nace con esta HU) con módulo `media_asset.py`:
  - `MediaType` (StrEnum): `PHOTO` | `VIDEO`.
  - `Orientation` (StrEnum): `VERTICAL` | `HORIZONTAL` | `SQUARE` — derivada de dimensiones.
  - `MediaAsset` (`@dataclass(frozen=True, slots=True)`): `media_type`, `width`, `height`,
    `content_hash`, `source` (Path) + propiedad `orientation`.
- Invariantes fail-fast en `__post_init__` (ValueError con mensaje accionable):
  `width ≥ 1`, `height ≥ 1`, `content_hash` no vacío.
- API pública re-exportada en `core/__init__.py`; docstrings en toda la API.
- Tests unitarios contra los CA (§11) + capa secundaria de boundary values, etiquetada.

### 2.2 OUT — NO entra (delimitaciones)
- Metadatos extendidos de video (duración, fps, codec) → HU-014.
- Cálculo real del hash (algoritmo, IO) → HU-006; aquí el hash es un valor recibido.
- Lectura de EXIF / detección de orientación desde archivo → HU-004/005 (E1).
- `QualityReport`, `Transform`, `BusinessProfile` → HU-158/159/160.
- Serialización del catálogo → HU-012 (tras ADR HU-153).
- Jerarquía de excepciones del dominio → HU-161 (ver RN-4).

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | Asset cuadrado (ni V ni H) | `Orientation.SQUARE` — tercer valor explícito, no un caso especial de V/H | Maestro §7 (formatos 1:1 existen en el dominio general; el perfil del cliente 0 los excluye como *salida*, no como *entrada*) |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- Idioma de los identificadores públicos → P-1.
- Formato/algoritmo del hash (¿validar hex?) → P-2.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `src/media_optimizer/core/__init__.py` | nuevo | bajo | ✅ `core/` no existe en `develop` (5c8a532) |
| `src/media_optimizer/core/media_asset.py` | nuevo | bajo | ✅ ídem |
| `tests/core/test_media_asset.py` | nuevo | bajo | ✅ `tests/` solo tiene smoke + stack_vision |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| Esqueleto HU-150 (mypy estricto, ruff con S/PTH/T20, pytest, coverage) | Sí | El contrato entra al harness sin tocar config |
| stdlib: `dataclasses`, `enum.StrEnum`, `pathlib.Path` | Sí | Cero dependencias nuevas — `core/` ni siquiera importa numpy |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| `MediaAsset` (en memoria; persistencia = HU-012) | nuevo contrato | media_type, width, height, content_hash, source | N/A — no hay BD; el "esquema real" es el backlog y sus HUs consumidoras (verificado en insumo §1) |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "`core/` … **sin IO**" · "sin importar OpenCV, ffmpeg ni filesystem" | CLAUDE.md módulos · `python.md` | No | Solo stdlib; `Path` como valor sin tocar disco; sin `numpy` |
| RN-2 | "contratos de dominio como dataclasses (frozen cuando aplique)" | `python.md` | No | `frozen=True, slots=True`; igualdad por valor |
| RN-3 | "fail fast en violaciones de contrato" | `python.md` | No | `__post_init__` valida invariantes y lanza `ValueError` con mensaje claro |
| RN-4 | "corrupto ≠ inválido ≠ bug" (excepciones = HU-161) | backlog HU-161 | No | Violar el contrato ES un bug ⇒ `ValueError` permanece incluso tras HU-161 (que cubre errores de datos del usuario, no de programación) |
| RN-5 | Orientación V/H como dato del dominio | backlog HU-005 · Maestro §8.2 | No | Propiedad pura derivada: `height > width` ⇒ V · `width > height` ⇒ H · igual ⇒ SQUARE |
| RN-6 | Cobertura ≥95% en dominio puro | CLAUDE.md Pre-Flight | No | Evidencia con `pytest --cov` en el cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | `width ≥ 1` y `height ≥ 1` | `ValueError` con el valor recibido en el mensaje |
| V-2 | `content_hash` no vacío (tras strip) | `ValueError` |
| V-3 | Inmutabilidad: asignar un campo lanza `FrozenInstanceError` | test lo garantiza |

---

## 6. Preguntas abiertas

### P-1 — ¿Identificadores públicos en inglés (`width`, `content_hash`, `source`) con docstrings en español?
- **Categoría:** INFORMATIVA
- **Importa porque:** fija la convención de naming de TODO el dominio desde el primer contrato.
- **Va dirigida a:** @oscardacto.
- **Mi mejor hipótesis:** sí — los nombres de los contratos ya son ingleses por constitución (`MediaAsset`, `QualityReport` en CLAUDE.md); mezclar `MediaAsset.ancho` sería inconsistente. Docs y specs siguen en español.
- **Si se asume mal, costo:** rename mecánico temprano (1 archivo hoy).
- **Estado:** ABIERTA

### P-2 — ¿El contrato valida formato del hash (hex, longitud) o solo no-vacío?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** solo no-vacío — el algoritmo (y por tanto formato/longitud) lo decide HU-006; sobre-validar aquí acoplaría el contrato a una decisión que aún no existe.
- **Si se asume mal, costo:** añadir validación después es aditivo, no rompe consumidores.
- **Estado:** ABIERTA

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Naming inglés + docstrings español (patrón ya sembrado en tests de HU-150/152: funciones de test en español, código en inglés) | P-1 | Rename de 1 módulo |
| A-2 | Hash como `str` opaco no vacío | P-2 | Validación aditiva posterior |
| A-3 | `StrEnum` (3.11+) para serialización natural futura (HU-012: JSON directo) | — | Cambio a `Enum` clásico trivial |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | El contrato resulta insuficiente para HU-158/159 (campos faltantes) y fuerza cambios | técnico | media | bajo | Composición: los contratos siguientes envuelven `MediaAsset`, no lo modifican; extensión aditiva |
| R-2 | Sobre-diseño (añadir campos "por si acaso") | técnico | media | medio | El alcance está clavado a los 4 conceptos literales del ticket; todo extra → OUT |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (2 INFORMATIVAS)
- **Asunciones tomadas:** 3
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop 5c8a532`: sin `core/`, harness verde con 3 tests)
  - [x] HUs consumidoras cruzadas en el backlog (158/159/001/005/006/012 — insumo §1)
  - [x] Reglas de pureza de `core/` cruzadas (CLAUDE.md + python.md, citadas en RN-1)
  - [x] Componentes reutilizables buscados (§3.1 — stdlib pura, cero dependencias nuevas)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 92% — el 8%: P-1 (convención de naming, reversible) y R-1 (suficiencia para contratos siguientes).

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-150 | Consume el esqueleto | DONE |
| HU-158, HU-159 | Componen con este contrato | backlog (siguientes) |
| HU-001/005/006/012 | Lo consumen desde E1 | backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna (stdlib pura).

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — Construcción válida para foto y video
- **Given:** valores válidos (p. ej. foto 1080×1920, hash no vacío, `Path` de origen)
- **When:** se construye `MediaAsset` con `MediaType.PHOTO` y con `MediaType.VIDEO`
- **Then:** el objeto expone los 4 conceptos del ticket tal como se recibieron

### CA-2 — Inmutabilidad
- **Given:** un `MediaAsset` construido
- **When:** se intenta asignar cualquier campo
- **Then:** `FrozenInstanceError`

### CA-3 — Invariantes fail-fast
- **Given:** `width=0`, `height=-1` o `content_hash=""`
- **When:** se construye
- **Then:** `ValueError` inmediato cuyo mensaje nombra el campo y el valor recibido

### CA-4 — Orientación derivada correcta
- **Given:** dimensiones 1080×1920 / 1920×1080 / 1000×1000
- **When:** se consulta `orientation`
- **Then:** `VERTICAL` / `HORIZONTAL` / `SQUARE` respectivamente

### CA-5 — Igualdad por valor
- **Given:** dos `MediaAsset` con los mismos campos, y un tercero que difiere en uno
- **Then:** los dos primeros son iguales (y comparten hash de objeto); el tercero no

### CA-6 — Pureza de `core/` y tipado
- **When:** se inspeccionan los imports de `core/` y corre `mypy src/` (estricto)
- **Then:** solo stdlib (`dataclasses`, `enum`, `pathlib`) y mypy exit 0

### CA-7 — Cobertura de dominio puro
- **When:** `uv run pytest --cov=media_optimizer.core`
- **Then:** cobertura de `core/` ≥ 95%

### CA-8 — La batería completa sigue verde
- **When:** pytest · ruff check + format --check · mypy
- **Then:** todo exit 0

### CA-9 — Trazabilidad del ciclo
- **Then:** gate-log con `draft`, `gate_spec` y `dev` de HU-157

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial y evaluación de gate | Claude (ejecutor) |
| 2026-07-26 | DEV: implementado según §2.1 sin desviaciones (A-1 y A-2 aplicadas); 17 tests, cobertura core/ 100%, batería verde | Claude (ejecutor) |
