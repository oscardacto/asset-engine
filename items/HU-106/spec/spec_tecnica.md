# Spec Técnica `HU-106` — `Recorte de escenas a duración objetivo`

> **Estado:** LISTA PARA DEV · **Fecha:** 2026-09-06 · **Confianza global:** 92%

---

## 1. Resumen ejecutivo

- **Qué se pide:** ajustar un conjunto de escenas para que sumen exactamente la duración que
  pide el formato — 15, 30 o 60 segundos.
- **Para quién:** HU-105 (secuenciado por tramos), HU-107 (ensamblado).
- **Módulo:** `media_optimizer.core.scene_trimmer` — dominio puro, sin IO.
- **No obvio — «exacto» y «coma flotante» no conviven.** Medido: recortar tres escenas
  proporcionalmente a 15 s da **15.000000000000002**. Un reel que promete durar 15 s y dura
  eso falla cualquier comparación exacta, que es justo lo que el charter §6.1 verifica. **La
  aritmética va en milisegundos enteros** y el residuo de la división se asigna a una sola
  escena, así la suma cierra siempre.
- **Segundo punto no obvio: recortar puede producir escenas inservibles.** Encoger todo a la
  mitad convierte una escena de 1,2 s en una de 0,6 s, que en un reel es un parpadeo. Hay un
  mínimo por escena; las que no lo alcanzan se descartan y su tiempo se reparte entre las que
  quedan.

---

## 2. Alcance

### 2.1 IN
- `TrimStrategy`: cómo se recorta — proporcional o quitando del final.
- `TrimPlan`: el resultado, con qué se conservó y qué se descartó.
- `trim_to_target`: el ajuste.
- Mínimo por escena, como dato.

### 2.2 OUT
- **Aplicar el recorte al archivo de video** → HU-107, que ensambla. Aquí solo se decide
  qué tramo de cada escena se usa.
- **Elegir qué escena va en qué tramo del guion** → HU-105.
- **Alargar material que no llega a la meta** → repetir cuadros o ralentizar es otra cosa, y
  no tiene HU. Ver §4.
- **Los valores de duración por formato** → datos del perfil (HU-135); aquí son parámetros.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | El material suma **menos** que la meta | Se devuelve todo sin tocar; no se alarga nada |
| 2 | El material suma exactamente la meta | Se devuelve sin tocar; recortar cero es no recortar |
| 3 | Una escena queda bajo el mínimo al recortar | Se descarta y su tiempo se reparte |
| 4 | Todas quedarían bajo el mínimo | Se conservan las que quepan enteras, aunque no se llegue a la meta |
| 5 | Lote vacío | Plan vacío, no un error |
| 6 | Meta cero o negativa | `ValueError` |

---

## 3. Las dos estrategias, y cuándo sirve cada una

| Estrategia | Qué hace | Cuándo |
|---|---|---|
| **Proporcional** | Todas las escenas encogen en la misma proporción | Se quiere conservar el recorrido completo: aparecen todos los ambientes, cada uno más breve |
| **Quitar del final** | Se conservan enteras las primeras hasta llenar la meta; la que la cruza se recorta y el resto se descarta | Las escenas vienen ordenadas por calidad y se quiere que las mejores salgan **con su duración natural** |

Ninguna es mejor: **conservar todo lo visto** y **conservar bien lo mejor** son objetivos
distintos, y el perfil de negocio decidirá cuál aplica.

---

## 4. Por qué no se alarga el material corto

Si las escenas suman 9 s y la meta son 15, se devuelven los 9 s. Llegar a 15 exigiría repetir
cuadros o ralentizar, que **cambia lo que se ve** — y eso es una transformación de contenido,
no un ajuste de duración. No tiene HU y no se inventa aquí.

El plan informa que no alcanzó (`is_exact` en falso) para que quien llama pueda decidir: pedir
más material, aceptar un reel más corto, o repetir escenas. Esa decisión es suya, no de esta
función.

---

## 5. Modelo de datos

```
TrimPlan
├── scenes: tuple[Scene, ...]      las escenas ya ajustadas, en orden
├── target_seconds: float           lo que se pidió
├── strategy: TrimStrategy          cómo se recortó
└── dropped: tuple[int, ...]        índices de las escenas que se quedaron fuera

    .total_seconds   lo que suman de verdad
    .is_exact        si se alcanzó la meta al milisegundo
```

`is_exact` **se calcula**, no se guarda: no puede haber un plan que diga que cerró y no cierre.

---

## 6. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|-------|--------|-------------|
| RN-1 | `core/` puro, sin IO ni terceros | CLAUDE.md · hexagonal | Solo `dataclasses`, `enum` y `Scene` |
| RN-2 | Determinismo | charter §6.1 | Aritmética entera; mismo lote y meta ⇒ mismo plan |
| RN-3 | Duraciones y mínimos como datos | charter §3 | Parámetros, nada fijado en la lógica |
| RN-4 | No inventar contenido | charter §6.3 (espíritu) | No se alarga material que no existe |
| RN-5 | Cobertura 100% en dominio puro | Pre-Flight | Al cierre |

---

## 7. Criterios de aceptación en BDD

### CA-1 · El recorte proporcional cierra al milisegundo
```gherkin
DADO QUE una suma de duraciones escaladas en coma flotante no da un número redondo
CUANDO se recortan varias escenas proporcionalmente a una meta
ENTONCES la suma de las escenas resultantes es exactamente la meta
```

### CA-2 · Quitar del final conserva las primeras con su duración natural
```gherkin
DADO QUE las escenas llegan ordenadas por calidad
CUANDO se recorta quitando del final
ENTONCES las primeras conservan su duración original y solo se ajusta la que cruza la meta
```

### CA-3 · Material más corto que la meta no se alarga
```gherkin
DADO QUE alargar exigiría repetir cuadros o ralentizar, que cambia lo que se ve
CUANDO las escenas suman menos que la meta
ENTONCES se devuelven todas sin tocar, y el plan informa que no se alcanzó
```

### CA-4 · Material que ya suma la meta no se toca
```gherkin
DADO QUE recortar cero es no recortar
CUANDO las escenas suman exactamente la meta
ENTONCES se devuelven idénticas y el plan informa que se alcanzó
```

### CA-5 · Una escena que quedaría demasiado corta se descarta
```gherkin
DADO QUE una escena de dos décimas de segundo es un parpadeo, no un plano
CUANDO el recorte la dejaría bajo el mínimo
ENTONCES se descarta, su índice queda registrado, y su tiempo se reparte entre las demás
```

### CA-6 · El plan dice qué quedó fuera
```gherkin
DADO QUE quien llama necesita poder explicar el resultado
CUANDO alguna escena se descarta
ENTONCES el plan enumera sus índices
```

### CA-7 · El ajuste es determinista
```gherkin
DADO QUE el pipeline promete la misma salida ante la misma entrada
CUANDO se ajusta dos veces el mismo lote a la misma meta
ENTONCES ambos planes son idénticos
```

### CA-8 · Una meta imposible falla al pedirla
```gherkin
DADO QUE una duración objetivo de cero o negativa no significa nada
CUANDO se pide ajustar a esa meta
ENTONCES falla de inmediato, antes de tocar ninguna escena
```

---

## 8. Asunciones

| # | Asunción | Costo si se rompe |
|---|----------|-------------------|
| A-1 | El milisegundo es precisión suficiente | Cambiar la constante de escala |
| A-2 | Dos estrategias cubren lo que el perfil pedirá | Añadir un valor al enumerado, aditivo |
| A-3 | El residuo puede ir a una sola escena | Repartirlo cuadro a cuadro; imperceptible a 30 cuadros por segundo |
| A-4 | Recortar una escena significa quedarse con su principio | Añadir un parámetro de anclaje |

---

## 9. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R-1 | Que la suma no cierre por coma flotante | **medida como real** | alto | Aritmética entera; CA-1 lo comprueba |
| R-2 | Que el recorte produzca escenas inservibles | alta | medio | Mínimo por escena; CA-5 |
| R-3 | Que se alargue material inexistente | media | alto (inventa contenido) | CA-3 |
| R-4 | Bucle infinito al descartar y recalcular | baja | alto | El descarte reduce el conjunto en cada vuelta; termina siempre |

---

## 10. Confianza global

- **Preguntas abiertas:** 0 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] **Pérdida de precisión medida**, no supuesta: 15.000000000000002
  - [x] `Scene` leído en código: `index`, `start_seconds`, `end_seconds`, `duration_seconds`
  - [x] Bloqueo de HU-105 confirmado: los 6 tramos del guion declaran ambiente
  - [x] Consumidores (HU-105, HU-107) revisados en el backlog
- **Recomendación:** ✅ **LISTA PARA DEV. Confianza 92%.** El 8% es A-2 y A-4.

---

## 11. Dependencias
| ID | Relación | Estado |
|----|----------|--------|
| HU-101 | `Scene` | DONE |
| HU-103 | Las escenas que sobreviven al descarte | DONE |
| HU-105 | La llamará por tramo — **bloqueada por HU-032** | backlog |
| HU-107 | Aplicará el recorte al archivo | backlog |

---

## 12. Historial de cambios
| Fecha | Cambio | Por |
|-------|--------|-----|
| 2026-09-06 | Creación; se adelanta a HU-105 porque su núcleo no necesita el guion | Claude (ejecutor) |
