# Spec Técnica `HU-166` — `Generador de fixtures sintéticos de imagen (exposiciones, orientaciones, corruptos)`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 90% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** un generador determinista de imágenes sintéticas con propiedades
  controladas en los 3 ejes del ticket: exposición (brillo medio objetivo), orientación
  (dimensiones) y corrupción (truncado, magic bytes falsos) — la materia prima de los
  tests de E1/E2 sin tocar jamás medios reales del cliente (charter §6.6).
- **Para quién:** HU-020–022 (métricas de exposición), HU-005 (orientación), HU-002/009
  (formatos hostiles y corruptos), HU-038/164 (golden tests), HU-185 (dataset E2E).
- **Módulo / dominio:** nuevo paquete `media_optimizer.testing` — infraestructura de
  plataforma (numpy/cv2 permitidos; NO es `core/`). Cobertura exigida ≥80%.
- **No obvio (lo crítico que el ticket no dice de frente):** el generador debe producir
  propiedades **verificables con exactitud conocida**: una imagen plana tiene brillo
  medio *exacto* (para calibrar la paridad ±2% de HU-020 hace falta un caso sin ruido) y
  una texturizada lo tiene *aproximado con tolerancia declarada*. Y "corrupto" no es un
  solo caso: truncado a mitad de stream ≠ magic bytes falsos ≠ vacío — cada uno ejercita
  una rama distinta de la ingesta (decodificador vs validador de formato vs tamaño).

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- Paquete `src/media_optimizer/testing/` con `synthetic.py`:
  - `flat_image(width, height, brightness)` — brillo medio **exacto** (sin ruido).
  - `textured_image(width, height, mean_brightness, seed, spread=...)` — ruido con
    semilla, brillo medio ≈ objetivo (tolerancia declarada en docstring y testeada).
  - `encode_jpeg(image, quality=90) -> bytes` · `write_jpeg(path, image, quality=90)`.
  - `truncated_jpeg(image, keep_fraction=0.5) -> bytes` — JPEG cortado a mitad de stream.
  - `not_an_image(size=256) -> bytes` — bytes deterministas sin magic válido.
- Invariantes fail-fast (`ValueError`): dims ≥1, brillo en [0, 255], quality en [1, 100],
  keep_fraction en (0, 1), size ≥1.
- Determinismo: misma semilla ⇒ mismos arrays ⇒ mismos bytes JPEG (wheel lockeado).
- Meta-tests del generador (el generador también se testea) + capa secundaria.

### 2.2 OUT — NO entra (delimitaciones)
- **EXIF sintético** (Orientation, fechas) → cv2 no escribe EXIF; llegará con HU-004/005,
  posiblemente con dependencia nueva (⇒ ADR) — ver P-2.
- Fixtures de video → HU-167 (P2).
- Framework de golden tests que los consume → HU-164.
- Casos WhatsApp específicos (1288×952, prefijo WA) → HU-007 los compone con este generador.
- Fixtures pytest/conftest compartidos → los definirá cada HU consumidora según necesite.

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | Exposiciones extremas (negro 0 / blanco 255) | `flat_image` las produce exactas; en `textured_image` el clipping desplaza la media ⇒ tolerancia solo garantizada en rango medio (documentado) | HU-021/022 (aplastado/quemado) |
| 2 | Corrupto ≠ inválido | truncado (decodificador falla a medias) vs magic falso (formato inválido) vs vacío — generadores separados | HU-002 vs HU-009 |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- Ubicación del paquete (src vs tests/) → P-1.
- EXIF sintético → P-2.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `src/media_optimizer/testing/__init__.py` + `synthetic.py` | nuevo paquete | bajo | ✅ no existe en `develop` (7c02d28) |
| `tests/testing/test_synthetic.py` | nuevo | bajo | ✅ no existe |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| numpy 2.5.1 + opencv-headless 5.0 (lockeados, ADR-002) | Sí | `default_rng(seed)` + `imencode/imdecode` — cero dependencias nuevas |
| Patrón de invariantes fail-fast con mensajes accionables (core/) | Sí | Mismo estilo de ValueError |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| N/A — genera arrays y bytes, no persiste estado | — | — | N/A |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "fixtures de test sintéticos o libres" — jamás medios del cliente | charter §6.6 | No | Todo se genera por código; nada se descarga ni copia |
| RN-2 | "Determinismo: semillas fijas" | `python.md` | No | `np.random.default_rng(seed)` explícito en la firma; sin estado global |
| RN-3 | Paridad ±2% con auditoría manual (el consumidor calibra contra esto) | charter §7 · HU-020 | No | `flat_image` con media exacta (calibración) + `textured_image` con tolerancia declarada (realismo) |
| RN-4 | "magic bytes, no extensión" · "corruptos o truncados" | HU-002 · HU-009 | No | Corruptos diferenciados: magic falso / truncado / (vacío = trivial con `b""`, no necesita helper) |
| RN-5 | Cobertura ≥80% módulo tocado | CLAUDE.md Pre-Flight | No | Meta-tests del generador |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | dims ≥1 · brillo ∈ [0,255] · quality ∈ [1,100] · keep_fraction ∈ (0,1) · size ≥1 | `ValueError` nombrando parámetro y valor |
| V-2 | Un JPEG generado válido debe decodificar a las dimensiones pedidas | meta-test lo garantiza |

---

## 6. Preguntas abiertas

### P-1 — ¿El generador vive en `src/media_optimizer/testing/` o en `tests/support/`?
- **Categoría:** INFORMATIVA
- **Importa porque:** define quién puede importarlo.
- **Va dirigida a:** @oscardacto (ratificable en el PR).
- **Mi mejor hipótesis:** `src/media_optimizer/testing/` (patrón `numpy.testing`): lo
  consumen tests, `benchmarks/` (HU-165) y el dataset E2E (HU-185) — desde `tests/` no
  sería importable limpio; además queda bajo mypy estricto y ruff completos.
- **Si se asume mal, costo:** mover un paquete pequeño + ajustar imports (mecánico).
- **Estado:** ABIERTA

### P-2 — ¿Se necesita EXIF sintético (Orientation) ya en esta HU?
- **Categoría:** IMPORTANTE (para HU-004/005, no para esta)
- **Importa porque:** HU-004/005 testearán EXIF malformado/Orientation y cv2 **no escribe
  EXIF** — implicará o bytes EXIF crafteados a mano o una dependencia nueva (⇒ ADR).
- **Mi mejor hipótesis:** no aquí — ninguna consumidora inmediata (HU-020–022, HU-002/009)
  lo usa; adelantarlo sería decidir una dependencia sin su HU.
- **Si se asume mal, costo:** extensión aditiva del generador cuando HU-004 la especifique.
- **Estado:** ABIERTA (transferida como nota de dependencia a HU-004/005)

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Paquete en `src/media_optimizer/testing/` | P-1 | Mover paquete (mecánico) |
| A-2 | Sin EXIF en esta HU | P-2 | Extensión aditiva en HU-004 |
| A-3 | JPEG como único formato de salida (dominio celular; PNG llegará si un golden test lo exige) | — | Función `write_png` aditiva |
| A-4 | La tolerancia de `textured_image` se declara ±2 sobre el objetivo en rango medio [30, 225] | — | Ajustar spread/algoritmo (interno) |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | JPEG truncado que aún decodifica parcialmente (libjpeg es tolerante) | técnico | alta | bajo | El CA se formula honesto: "no reconstruye el original" (None **o** imagen distinta); el caso "garantizado ilegible" lo da `not_an_image` |
| R-2 | Bytes JPEG no reproducibles entre versiones de OpenCV | datos | baja | medio | El wheel está lockeado (ADR-002); el meta-test de determinismo detectaría el cambio en cualquier re-lock |
| R-3 | Media de `textured_image` fuera de tolerancia cerca de 0/255 por clipping | técnico | alta | bajo | Documentado + tolerancia garantizada solo en rango medio (A-4); los extremos exactos los da `flat_image` |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (1 IMPORTANTE transferida a HU-004, 1 INFORMATIVA)
- **Asunciones tomadas:** 4
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop 7c02d28`: 57 tests verdes, stack de visión operativo)
  - [x] Consumidores por eje cruzados en el backlog (insumo §2)
  - [x] Capacidad real del stack verificada (imencode/imdecode ya ejercitados en test_stack_vision)
  - [x] Componentes reutilizables buscados (§3.1 — cero dependencias nuevas)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 90% — el 10%: R-1/R-3 (semánticas de tolerancia, mitigadas por formulación honesta de los CA) y P-1 (ubicación).

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-150 / ADR-002 | Esqueleto + stack de visión | DONE / Aceptado |
| HU-020–022, HU-005, HU-002/009, HU-038, HU-164, HU-185 | Consumen los fixtures | backlog |
| HU-004/005 | Heredan la pregunta del EXIF sintético (P-2) | backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna.

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — Exposiciones controladas
- **Given:** `flat_image(100, 100, brightness=40)` y `textured_image(256, 256, mean_brightness=120, seed=7)`
- **Then:** la plana tiene brillo medio **exactamente** 40; la texturizada, 120 ± 2

### CA-2 — Orientaciones por dimensiones
- **When:** se generan 1080×1920, 1920×1080 y 1000×1000
- **Then:** los arrays tienen `shape` (alto, ancho, 3) correcto para V / H / cuadrada

### CA-3 — Corruptos diferenciados
- **Given:** un JPEG válido, uno truncado (`keep_fraction=0.5`) y `not_an_image()`
- **Then:** el válido decodifica a sus dimensiones; el truncado **no reconstruye el original** (decodifica a None o a imagen distinta); el de magic falso decodifica a None

### CA-4 — Determinismo byte a byte
- **Given:** dos llamadas con la misma semilla y parámetros
- **Then:** arrays idénticos y bytes JPEG idénticos; semilla distinta ⇒ bytes distintos

### CA-5 — Invariantes fail-fast
- **Given:** brillo 300, quality 0, keep_fraction 1.0 o dims 0
- **Then:** `ValueError` inmediato nombrando parámetro y valor

### CA-6 — Tipado y lint
- **Then:** `mypy src/` estricto exit 0 (numpy typing incluido) · ruff limpio

### CA-7 — Cobertura del módulo ≥80%
- **Then:** `pytest --cov=media_optimizer.testing` ≥ 80%

### CA-8 — Trazabilidad
- **Then:** gate-log con `draft`, `gate_spec`, `dev` de HU-166

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial y evaluación de gate | Claude (ejecutor) |
