# Spec Técnica `HU-160` — `Contrato BusinessProfile en core/`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Confianza global:** 87% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** la **forma** que tendrá un perfil de negocio. No sus datos.
- **Para quién:** 8 HUs declaradas (008, 029, 033, 070, 130, 132, 133, 134) y, por
  transitividad, las 23 que dependen de ellas. Es el contrato más consumido del proyecto
  después de `MediaAsset`.
- **Módulo:** `media_optimizer.core.business_profile` — dominio puro, sin IO.
- **No obvio — el error caro de esta HU no es un bug, es una forma equivocada.** Un
  contrato demasiado específico convierte el criterio de LIVING POP en código y rompe la
  regla del charter §3; uno demasiado genérico (`dict[str, Any]`) no contrata nada y traslada
  el problema entero a HU-130. **La línea correcta no es "cuántos campos" sino
  *quién sabe la respuesta*:** si el nombre lo conoce el código (una intención de salida
  existe porque hay una etapa que la produce), es estructura; si solo lo conoce el perfil
  (cuáles ambientes espera este negocio, cuánto pesa la nitidez), es dato abierto.

---

## 2. Alcance

### 2.1 IN
- `OutputIntent` (StrEnum): para qué se produce una salida — portada, feed, story.
- `OutputFormat` (frozen): intención + dimensiones objetivo en px. El aspecto **se deriva**
  de las dimensiones, no se declara aparte.
- `ScoringWeights` (frozen): pesos por métrica **para una intención**.
- `BusinessProfile` (frozen): identidad, ambientes esperados, formatos, pesos, umbrales.
- Invariantes de contrato (fail fast): nombres no vacíos, dimensiones ≥ 1, pesos finitos
  y no negativos, sin intenciones ni formatos duplicados.
- Accesores de dominio: `format_for(intent)`, `weights_for(intent)`, `threshold(name)`.

### 2.2 OUT
- **Cargar el perfil desde archivo** → HU-130/131. Este módulo no toca disco (`core/`).
- **Mensajes de error accionables para perfiles hostiles** → HU-136. Aquí un contrato roto
  levanta `ValueError`; traducirlo a algo que un humano pueda arreglar es de E6.
- **Defaults del sistema** → HU-131. Un perfil sin umbrales es un perfil válido y vacío,
  no un perfil que se autocompleta.
- **Los datos de LIVING POP** → HU-132.
- **Opciones de estilo del revelado** (sin HDR, curva, temperatura) → nacen con sus HUs de
  E3, igual que las subcarpetas del workspace nacieron con las suyas. Añadirlas es aditivo.
- **Plantillas narrativas** (HU-135, P1) → mismo criterio: sin consumidor, no entran.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Perfil sin ningún formato de salida | Válido estructuralmente; que sea *útil* lo juzga E6 |
| 2 | Dos formatos con la misma intención | `ValueError` — `format_for` no podría responder |
| 3 | Se pide un formato/peso de una intención que el perfil no cubre | Devuelve `None` / mapping vacío, no explota: el perfil decide qué salidas produce |
| 4 | Peso negativo o NaN | `ValueError` — invertiría el sentido del score en silencio |
| 5 | Métrica con peso `0.0` | Válida: "esta métrica no cuenta" es una decisión legítima del perfil |

---

## 3. Componentes

| Componente | Cambio | Verificado |
|---|---|---|
| `src/media_optimizer/core/business_profile.py` | nuevo | ✅ no existe en `develop` |
| `src/media_optimizer/core/__init__.py` | exporta los 4 nombres nuevos | ✅ leído |
| `tests/core/test_business_profile.py` | nuevo | ✅ no existe |

### 3.1 Reutilizables
| Componente | ¿Reutilizar? | Justificación |
|---|---|---|
| Patrón de `QualityReport.metrics` | **Sí** | Ya resuelve mapping ordenado + inmutable + validado (`MappingProxyType` sobre claves ordenadas). Los umbrales y los pesos son el mismo problema |
| `Orientation` (HU-157) | No importar | Un formato de salida tiene aspecto propio; derivar la orientación del formato es tarea de quien recorta (E4) |
| Estilo de `__post_init__` de `MediaAsset` | Sí | `ValueError` con el valor recibido en el mensaje |

---

## 4. Modelo de datos

```
BusinessProfile
├── name: str                       identidad del perfil ("hospedaje")
├── version: str                    versión del perfil, no del software
├── environments: tuple[str, ...]   ambientes esperados, ordenados y sin repetir
├── formats: tuple[OutputFormat, …] ordenados por intención
├── scoring: tuple[ScoringWeights,…] ordenados por intención
└── thresholds: Mapping[str, float] solo lectura, claves ordenadas

OutputFormat(intent, width, height) → aspect_ratio, accepts(w, h)
ScoringWeights(intent, weights)     → weight_for(metric)
```

Todo colección es tupla ordenada y todo mapping es de solo lectura: el perfil es dato
compartido entre etapas y **el determinismo del pipeline depende de que iterarlo dé
siempre el mismo orden** (charter §6.1).

### 4.1 Por qué el aspecto se deriva y no se declara
Declarar `aspect="4:5"` **y** `width/height` crea dos fuentes de verdad que pueden
contradecirse, y obliga a validar la coherencia entre ambas. Con `1080×1350` el aspecto es
un `@property` y el mínimo de resolución que HU-008 necesita es el propio par de
dimensiones. Un dato, dos lecturas.

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|-------|--------|-------------|
| RN-1 | Criterio del cliente = datos, nunca código | charter §3 | Cero nombres de ambiente, umbral o cliente en este módulo |
| RN-2 | `core/` sin IO | CLAUDE.md · hexagonal ligera | No importa `filesystem`, ni `Path` para leer |
| RN-3 | Determinismo | charter §6.1 | Orden estable en toda colección |
| RN-4 | Fail fast en violación de contrato; fail safe en datos del usuario | `python.md` | `ValueError` aquí; mensaje accionable en HU-136 |
| RN-5 | Cero valores hardcodeados | Pre-Flight | Las únicas constantes son las de validación estructural |
| RN-6 | Cobertura ≥95% en dominio puro | Pre-Flight | `core/` es dominio puro |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|-----------|----------|
| V-1 | Nombre y versión no vacíos | `ValueError` |
| V-2 | Dimensiones de formato ≥ 1 px | `ValueError` |
| V-3 | Una sola entrada por intención, en formatos y en pesos | `ValueError` |
| V-4 | Pesos finitos y ≥ 0 | `ValueError` |
| V-5 | Ambientes no vacíos y sin duplicados | `ValueError` |
| V-6 | Umbrales finitos con nombre no vacío | `ValueError` |

---

## 6. Preguntas abiertas

### P-1 — ¿`OutputIntent` cerrado o abierto?
- **Categoría:** IMPORTANTE (no bloqueante)
- **Mi mejor hipótesis:** **cerrado** (`StrEnum` con portada/feed/story). Una intención de
  salida no es criterio del cliente: existe porque hay una etapa del pipeline que la
  produce y un formato de red social que la consume. Abrirla a texto libre significaría
  que un perfil puede pedir una salida que ningún código sabe generar — el fallo aparecería
  tarde y sin explicación. Añadir una intención nueva es una línea, y viene acompañada de
  la etapa que la implementa.
- **Contraste:** los ambientes sí son abiertos, y por la razón simétrica — ninguna etapa
  produce "cocina"; el perfil es el único que sabe qué espera ver.
- **Costo si se asume mal:** cambiar un `StrEnum` por `str` y mover la validación a HU-130.
- **Estado:** ABIERTA (ratificable con HU-132, el primer perfil real)

### P-2 — ¿Los pesos deben sumar 1?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** **no se exige aquí**. Normalizar es decisión del algoritmo de
  score (HU-070): puede dividir por la suma y obtener el mismo resultado. Exigirlo en el
  contrato haría que ajustar un peso obligue a recalcular todos los demás a mano, que es
  exactamente el tipo de fricción que hace que la gente deje de tocar el perfil.
- **Estado:** ABIERTA

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|----------|-------------------|
| A-1 | `OutputIntent` cerrado (P-1) | Cambiar el tipo y mover validación a HU-130 |
| A-2 | Los pesos no se normalizan en el contrato (P-2) | Una línea en HU-070 |
| A-3 | Las dimensiones objetivo bastan para HU-008 ("bajo el nativo") | Añadir un campo, aditivo |
| A-4 | Umbrales como `Mapping[str, float]` cubren HU-029 y HU-133 | Si un umbral necesitara ser un rango, sería un tipo nuevo — aditivo |
| A-5 | Estilo de revelado y plantillas narrativas entran con sus HUs | Añadir campos con default, aditivo |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R-1 | Sobreajuste a LIVING POP | media | **alto** (rompe la premisa del charter) | Test explícito: se construye un perfil de una vertical distinta (bar nocturno, criterios opuestos) y debe caber sin tocar el módulo |
| R-2 | El contrato se queda corto y E6 lo reabre | media | medio | Los 8 consumidores se leyeron uno a uno; lo omitido está listado en 2.2 con su HU |
| R-3 | Mapping mutable filtrado al dominio | baja | medio | `MappingProxyType` sobre copia, patrón ya probado en `QualityReport` |
| R-4 | Iteración no determinista del perfil | baja | **alto** (rompe reproducibilidad) | Orden estable en construcción + test |

---

## 9. Confianza global

- **Preguntas abiertas:** 2 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] Los 8 consumidores leídos en el backlog, uno a uno
  - [x] Charter §3 (generalización) y §6.1 (determinismo) leídos
  - [x] `core/` leído: estilo, exports e invariantes existentes
  - [x] Frontera con E6 confirmada en el enunciado del backlog ("datos en E6")
  - [x] Patrón de mapping inmutable verificado en código, no supuesto
- **Recomendación:** ✅ **LISTA PARA DEV**
- **Confianza: 87%.** El 11% restante es P-1 y R-2: son decisiones de forma que solo el
  primer perfil real (HU-132) ratifica del todo. El 2% es A-3.

---

## 10. Dependencias
| ID | Relación | Estado |
|----|----------|--------|
| HU-150 | Esqueleto del paquete | DONE |
| HU-157 | Estilo de contratos de `core/` | DONE |
| HU-130, HU-131, HU-132, HU-136 | Cargarán y poblarán esta estructura | backlog |
| HU-008, HU-029, HU-033, HU-070, HU-133, HU-134 | La consumirán | backlog |

---

## 11. Criterios de aceptación

- **CA-1** — `BusinessProfile` es inmutable y sus colecciones iteran en orden estable.
- **CA-2** — `format_for(intent)` devuelve el formato de esa intención, o `None` si el perfil no la cubre.
- **CA-3** — `weights_for(intent)` devuelve los pesos de esa intención, vacío si no la cubre.
- **CA-4** — `threshold(name)` devuelve el umbral, o el default indicado si no está.
- **CA-5** — El aspecto de un formato se deriva de sus dimensiones (`1080×1350` ⇒ 0.8).
- **CA-6** — Duplicar una intención, en formatos o en pesos, levanta `ValueError`.
- **CA-7** — Peso negativo, NaN o infinito levanta `ValueError`; `0.0` es válido.
- **CA-8** — Nombre, versión, ambiente o métrica vacíos levantan `ValueError`.
- **CA-9** — Un perfil de una vertical **distinta a hospedaje** se construye sin tocar el módulo.
- **CA-10** — `core/` sigue sin IO: el test de gobernanza pasa.
- **CA-11** — Cobertura ≥95% en el módulo y batería verde.
- **CA-12** — Trazabilidad en el gate-log.

---

## 12. Historial de cambios
| Fecha | Cambio | Por |
|-------|--------|-----|
| 2026-07-26 | Creación | Claude (ejecutor) |
