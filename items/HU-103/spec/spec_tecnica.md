# Spec Técnica `HU-103` — `Descarte de escenas malas con causas`

> **Estado:** LISTA PARA DEV · **Fecha:** 2026-09-06 · **Confianza global:** 91%

---

## 1. Resumen ejecutivo

- **Qué se pide:** decidir qué escenas sirven y, sobre todo, **por qué no** sirven las otras.
- **Para quién:** HU-105 (secuenciado) y HU-110 (reporte de escenas usadas y descartadas).
- **Módulo:** `media_optimizer.core.scene_selection` — dominio puro, sin IO.
- **No obvio — la causa es el entregable, no el veredicto.** Un descarte sin causa le dice al
  usuario que su clip no sirve; con causa le dice **qué grabar mejor la próxima vez**. Por eso
  se reportan **todas** las causas de una escena, no la primera que falla: una toma corta *y*
  temblorosa tiene dos cosas que corregir.
- **Segundo punto no obvio: el umbral no puede ir sobre la nota general.** HU-102 dejó
  anotado que esa nota promedia solo los componentes disponibles y que **cambiará de valor
  cuando entre la nitidez** (HU-023). Un umbral sobre ella se comportaría distinto ese día
  sin que nadie tocara nada. Los umbrales van **por componente**.

---

## 2. Alcance

### 2.1 IN
- `DiscardReason`: las causas posibles, como enumerado cerrado.
- `SceneThresholds`: los umbrales, como datos.
- `SceneVerdict`: qué se decidió sobre una escena y por qué.
- `judge_scene` / `select_scenes`: el juicio, escena a escena y por lote.
- Ayudas de lectura sobre el lote: qué sobrevive y qué se descarta.

### 2.2 OUT
- **Calibrar los umbrales con material del cliente** → HU-133; aquí son datos con un valor
  por defecto justificado por lo medido.
- **Detectar o puntuar escenas** → HU-101 y HU-102, ya cerradas.
- **Ordenar las que sobreviven** → HU-105.
- **El reporte legible** → HU-110.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Escena que falla por varias razones | Se reportan **todas**, en orden estable |
| 2 | Lote donde todo se descarta | Es un resultado válido, no un error: dice que hay que volver a grabar |
| 3 | Escena justo en el umbral | Se conserva: el umbral es el mínimo aceptable, no el primer rechazo |
| 4 | Umbrales imposibles (fuera de 0–1) | `ValueError` al construir |

---

## 3. Umbrales por defecto, y por qué esos

Fijados con lo que HU-102 midió sobre 19 escenas reales del cliente, **no a ojo**:

| Umbral | Valor | Justificación |
|--------|------:|---------------|
| `min_duration_seconds` | **1.5** | El video largo produjo 5 escenas por debajo de eso; con un umbral de detección más alto desaparecen. Son paneo cruzando el detector, no cortes |
| `min_stability` | **0.15** | La estabilidad real llega **como máximo a 0.404**. Un valor de 0.5 descartaría las 19 escenas. Con 0.15 se apartan las peores sin vaciar el lote |
| `min_exposure` | **0.60** | El material real va de 0.799 a 0.976: nada se descarta hoy por luz, que es lo correcto — el problema del cliente no es la exposición |

**Ninguno es un número mágico**: los tres son datos del perfil, y HU-133 los calibrará con más
material. Estos valores son el punto de partida defendible, no el definitivo.

---

## 4. Modelo de datos

```
SceneThresholds(min_duration_seconds, min_exposure, min_stability)   ← datos del perfil

SceneVerdict
├── scene_index: int
├── keep: bool
└── reasons: tuple[DiscardReason, ...]   ← vacío si se conserva; TODAS las causas si no

DiscardReason = TOO_SHORT · POOR_EXPOSURE · UNSTABLE
```

**`keep` se deriva de `reasons`, no se guarda aparte.** Así no puede existir una escena
marcada como conservada que a la vez traiga causas de descarte: el estado imposible no se
puede construir.

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|-------|--------|-------------|
| RN-1 | `core/` puro, sin IO ni terceros | CLAUDE.md · hexagonal | Ni ffmpeg, ni OpenCV, ni la librería de escenas |
| RN-2 | Umbrales y pesos como datos | charter §3 | `SceneThresholds` los recibe; nada hardcodeado en la lógica |
| RN-3 | Determinismo | charter §6.1 | Las causas salen en orden fijo, no según un conjunto |
| RN-4 | Un fallo del material degrada, no tumba | charter | Descartar es un resultado normal, nunca una excepción |
| RN-5 | Cobertura 100% en dominio puro | Pre-Flight | Al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|-----------|----------|
| V-1 | Los umbrales de 0–1 están en rango | `ValueError` |
| V-2 | La duración mínima es positiva | `ValueError` |
| V-3 | `keep` es coherente con `reasons` | Imposible por construcción |

---

## 6. Criterios de aceptación en BDD

### CA-1 · Una escena buena se conserva sin causas
```gherkin
DADO QUE una escena supera todos los umbrales del perfil
CUANDO se la juzga
ENTONCES se conserva y no trae ninguna causa de descarte
```

### CA-2 · Una escena corta se descarta por su duración
```gherkin
DADO QUE una toma más breve que el mínimo suele ser un barrido de cámara y no un plano
CUANDO se juzga una escena por debajo de esa duración
ENTONCES se descarta indicando que fue demasiado corta
```

### CA-3 · Una escena temblorosa se descarta por estabilidad
```gherkin
DADO QUE el material se graba a pulso
CUANDO la estabilidad de una escena queda por debajo del mínimo
ENTONCES se descarta indicando que la cámara no estaba lo bastante quieta
```

### CA-4 · Se reportan todas las causas, no la primera
```gherkin
DADO QUE saber qué corregir es el valor del descarte
CUANDO una escena falla por más de un motivo
ENTONCES el veredicto los enumera todos, siempre en el mismo orden
```

### CA-5 · El umbral es el mínimo aceptable
```gherkin
DADO QUE un valor justo en el límite cumple el criterio
CUANDO una escena marca exactamente el umbral
ENTONCES se conserva
```

### CA-6 · El juicio no depende de la nota general
```gherkin
DADO QUE la nota general cambiará de valor cuando se añada una métrica nueva
CUANDO se juzgan dos escenas con la misma nota general pero componentes distintos
ENTONCES el veredicto puede diferir, porque mira cada componente por separado
```

### CA-7 · Un lote entero descartado es un resultado válido
```gherkin
DADO QUE un lote puede estar mal grabado de principio a fin
CUANDO ninguna escena supera los umbrales
ENTONCES se devuelven todos los veredictos con sus causas, sin error
```

### CA-8 · Los umbrales por defecto no vacían el material real
```gherkin
DADO QUE la estabilidad real del cliente llega como máximo a 0.404
CUANDO se aplican los umbrales por defecto a esa escala de valores
ENTONCES sobreviven escenas: el umbral aparta las peores, no el lote entero
```

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|----------|-------------------|
| A-1 | Tres causas cubren lo que hoy se puede medir | Añadir un valor al enumerado, aditivo |
| A-2 | Los umbrales por defecto sirven de punto de partida | Son datos; HU-133 los ajusta |
| A-3 | La nitidez entrará como una causa más sin tocar el contrato | Es el diseño: umbrales por componente |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R-1 | Un umbral mal puesto vacíe el lote | **alta si se fija a ojo** | alto | Valores derivados de 19 escenas reales; CA-8 lo comprueba |
| R-2 | Que el juicio cuelgue de la nota general | media | alto (se rompería al llegar HU-023) | CA-6 lo verifica explícitamente |
| R-3 | Que se reporte solo la primera causa | media | medio (pierde el valor del descarte) | CA-4 |

---

## 9. Confianza global

- **Preguntas abiertas:** 0 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] `items/HANDOFF.md` leído: los tres avisos de HU-102 están incorporados al diseño
  - [x] `SceneScore` y `Scene` leídos en código
  - [x] Rangos reales de las métricas tomados de la validación de HU-102 sobre 19 escenas
  - [x] Consumidores (HU-105, HU-110) revisados en el backlog
- **Recomendación:** ✅ **LISTA PARA DEV. Confianza 91%.** El 9% es A-2: los umbrales son un
  punto de partida medido, no una calibración cerrada.

---

## 10. Dependencias
| ID | Relación | Estado |
|----|----------|--------|
| HU-102 | `SceneScore` con componentes separados | DONE |
| HU-101 | `Scene` | DONE |
| HU-133 | Calibrará los umbrales | backlog |
| HU-105, HU-110 | La consumirán | backlog |

---

## 11. Historial de cambios
| Fecha | Cambio | Por |
|-------|--------|-----|
| 2026-09-06 | Creación, con los umbrales derivados de la validación real de HU-102 | Claude (ejecutor) |
