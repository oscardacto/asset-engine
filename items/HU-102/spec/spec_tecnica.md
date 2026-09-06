# Spec Técnica `HU-102` — `Score técnico por escena`

> **Estado:** LISTA PARA DEV · **Fecha:** 2026-09-06 · **Confianza global:** 87%

---

## 1. Resumen ejecutivo

- **Qué se pide:** puntuar cada escena de un clip para poder elegir las buenas y descartar
  las malas.
- **Para quién:** HU-103 (descarte con causas), HU-105 (secuenciado narrativo).
- **Módulos:** `core.scene_score` (contrato puro) · `video.scene_scoring` (el muestreo real).
- **No obvio — el enunciado pide una métrica cuya decisión no está tomada.** Pide nitidez,
  pero **HU-023 es un `ADR` sin cerrar** que decide *cómo* medirla (varianza de Laplaciano
  frente a Tenengrad), y HU-102 ni siquiera la declara como dependencia. Implementarla aquí
  sería tomar una decisión de stack saltándose su ADR. El score nace **extensible** para que
  la nitidez entre como un componente más sin tocar nada.
- **Segundo punto no obvio:** un score por escena no puede leer el clip entero — el charter
  prohíbe cargar video completo a RAM. Se muestrean unos pocos frames repartidos por la
  escena, saltando a sus posiciones.

---

## 2. Alcance

### 2.1 IN
- `SceneScore`: contrato con los componentes medidos y el score compuesto.
- `score_scene`: muestrea frames de una escena y la puntúa.
- `score_scenes`: lo mismo para todas las escenas de un clip.
- **Exposición** (reutiliza HU-029) y **estabilidad** (nueva).

### 2.2 OUT
- **Nitidez** → HU-023, que es quien decide cómo medirla. El contrato deja el hueco.
- **Descarte con causas** → HU-103.
- **Ingesta de clips con streaming** → HU-100. Aquí solo se muestrean frames sueltos.
- **Los pesos del score** → datos del perfil (HU-134); aquí son parámetros.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Escena más corta que el número de muestras pedidas | Se muestrea lo que quepa, mínimo 1 frame |
| 2 | Un frame ilegible en mitad de la escena | Se salta ese frame; la escena se puntúa con el resto |
| 3 | Ningún frame legible | `CorruptMediaError`: esa escena se aparta, el clip sigue |
| 4 | Escena de un solo frame | La estabilidad es perfecta: no hay movimiento que medir |

---

## 3. Modelo de datos

```
SceneScore
├── scene_index: int          a qué escena corresponde
├── exposure: float [0,1]     qué tan bien expuesta (HU-029)
├── stability: float [0,1]    1 = quieta · 0 = temblorosa
├── sampled_frames: int       cuántos frames se miraron
└── overall: float [0,1]      la media de los componentes disponibles
```

**`overall` promedia solo los componentes que existen.** Cuando la nitidez entre con HU-023,
se suma al promedio y nada más cambia — ni el contrato ni quien lo consume.

---

## 4. Cómo se mide la estabilidad

Se compara cada frame muestreado con el anterior: si la imagen cambia poco, la cámara estaba
quieta. Es la diferencia media de luminosidad entre frames consecutivos, normalizada e
invertida — **más diferencia, menos estabilidad**.

Un clip de celular grabado a pulso tiene diferencia alta; uno sobre trípode, casi cero. Con
una sola muestra no hay nada que comparar, así que la estabilidad es 1: no se penaliza lo que
no se puede medir.

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|-------|--------|-------------|
| RN-1 | Nunca cargar el video completo a RAM | `python.md` · charter | Se salta a las posiciones y se leen frames sueltos |
| RN-2 | Un medio corrupto degrada, no tumba | charter | Frame ilegible se salta; escena sin frames se aparta |
| RN-3 | `core/` sin IO | CLAUDE.md | El contrato no abre nada |
| RN-4 | Determinismo | charter §6.1 | Las posiciones de muestreo se calculan, no se sortean |
| RN-5 | Umbrales y pesos como datos | charter §3 | Parámetros, no constantes de negocio |
| RN-6 | Cobertura ≥80% del módulo · 100% en `core/` | Pre-Flight | Al cierre |

---

## 6. Criterios de aceptación en BDD

### CA-1 · Una escena bien expuesta puntúa más que una oscura
```gherkin
DADO QUE la exposición es uno de los componentes del score
CUANDO se puntúan dos escenas idénticas salvo por su luminosidad
ENTONCES la que está cerca del objetivo del negocio obtiene mejor score
```

### CA-2 · Una escena quieta puntúa más estable que una temblorosa
```gherkin
DADO QUE un clip grabado a pulso se mueve entre cuadros
CUANDO se comparan una escena estática y otra con cambio fuerte entre cuadros
ENTONCES la estática obtiene mayor estabilidad
```

### CA-3 · El muestreo no lee el clip entero
```gherkin
DADO QUE el charter prohíbe cargar un video completo en memoria
CUANDO se puntúa una escena de varios segundos
ENTONCES se leen como mucho las muestras pedidas, no todos sus cuadros
```

### CA-4 · El score es determinista
```gherkin
DADO QUE el pipeline promete la misma salida ante la misma entrada
CUANDO se puntúa dos veces la misma escena del mismo clip
ENTONCES ambos resultados son idénticos
```

### CA-5 · Una escena muy corta se puntúa igual
```gherkin
DADO QUE una escena puede durar menos que el número de muestras pedidas
CUANDO se la puntúa
ENTONCES se usa al menos un cuadro y el resultado sigue siendo válido
```

### CA-6 · Una escena ilegible se aparta sin tumbar el clip
```gherkin
DADO QUE un archivo puede estar dañado
CUANDO ningún cuadro de la escena se puede leer
ENTONCES se levanta el error que aparta ese medio, y el resto del clip continúa
```

### CA-7 · El score compuesto solo promedia lo que se midió
```gherkin
DADO QUE la nitidez todavía no existe como métrica decidida
CUANDO se calcula el score general
ENTONCES promedia los componentes disponibles, y añadir uno nuevo no cambia el contrato
```

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|----------|-------------------|
| A-1 | Muestrear pocos frames representa la escena | Subir el número, es un parámetro |
| A-2 | La diferencia de luminosidad basta como estabilidad | Cambiar una función |
| A-3 | La nitidez entra después sin tocar el contrato | Es el diseño: promedio de lo disponible |
| A-4 | Saltar a una posición del clip es fiable en los formatos de celular | Se verifica con material real al cierre |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R-1 | Que se implemente nitidez saltándose el ADR de HU-023 | media | **alto** (decisión de stack sin ADR) | Explícitamente fuera de alcance; el contrato deja el hueco |
| R-2 | Que el muestreo cargue el clip entero | media | alto | CA-3 cuenta los cuadros leídos |
| R-3 | Saltar posiciones falle en algún formato | media | medio | Se valida con los 7 videos reales del cliente |
| R-4 | Estabilidad confunda paneo con temblor | alta | bajo | Es una aproximación declarada; HU-133 la calibra |

---

## 9. Confianza global

- **Preguntas abiertas:** 0 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] Estado real de las dependencias comprobado: HU-023 y HU-100 **no iniciadas**
  - [x] `exposure_score` y `ExposureThresholds` leídos en código (HU-029)
  - [x] `Scene` y el adaptador de HU-101 disponibles
  - [x] Charter: prohibición de cargar video completo a RAM
  - [x] Material real disponible para validar: 7 videos del cliente
- **Recomendación:** ✅ **LISTA PARA DEV. Confianza 87%.** El 13% es A-4 y R-4.

---

## 10. Dependencias
| ID | Relación | Estado |
|----|----------|--------|
| HU-101, HU-029 | Escenas y score de exposición | DONE |
| **HU-023** | **Decide cómo medir nitidez — dependencia no declarada en el backlog** | **no iniciada** |
| HU-103, HU-105 | La consumirán | backlog |

---

## 11. Historial de cambios
| Fecha | Cambio | Por |
|-------|--------|-----|
| 2026-09-06 | Creación; recorta la nitidez por depender de un ADR sin cerrar | Claude (ejecutor) |
