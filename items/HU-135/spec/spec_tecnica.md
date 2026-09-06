# Spec Técnica `HU-135` — `Plantillas narrativas como datos`

> **Estado:** LISTA PARA DEV · **Fecha:** 2026-09-05 · **Regularizada:** 2026-09-05
> **Confianza global:** 90%

> ⚠️ **Nota de honestidad procesal.** Esta spec se escribe **después** de que el código se
> implementara y se integrara a `develop` (`c92074d`), y de que la HU se marcara DONE. Eso
> incumple la Regla de Oro nº 1 del proyecto. Se documenta como regularización y así queda
> marcado en el gate-log: **no se presenta como si el gate se hubiera emitido a tiempo.**

---

## 1. Resumen ejecutivo

- **Qué se pide:** la forma del guion de un reel, y cómo se le asignan los clips de un lote.
- **Para quién:** HU-105 (secuenciado), HU-072 (orden de galería), HU-033 (cobertura).
- **Módulo:** `media_optimizer.video.templates`.
- **No obvio — qué hacer cuando falta material.** Un guion de seis tramos sobre un lote que
  solo cubre tres puede resolverse de dos formas: rellenar con los mejores clips
  disponibles, o **dejar el hueco**. Rellenar produce un reel completo que miente sobre la
  cobertura; dejar el hueco produce un reel más corto y **la lista exacta de lo que falta
  grabar**, que es justo lo que HU-033 necesita entregar al cliente.

---

## 2. Alcance

### 2.1 IN
- `NarrativeSlot`: un tramo — nombre, duración y ambiente esperado (opcional).
- `ReelTemplate`: el guion completo, con sus invariantes.
- `template_from_data`: construcción desde los datos del perfil, validados como no confiables.
- `SlotAssignment` / `Timeline`: el guion ya poblado, con sus huecos.
- `assign_slots`: el reparto de clips a tramos.
- `profiles/hospedaje/reel_template.json` como guion de ejemplo verificable.

### 2.2 OUT
- **Los datos definitivos del cliente 0** → HU-132.
- **Cargar el perfil desde disco** → HU-130/131.
- **Ejecutar el secuenciado sobre clips reales** → HU-105, bloqueada por ADR-006.
- **El etiquetado de ambientes** → HU-032; hasta entonces los tramos exigentes son huecos.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Un tramo sin ambiente declarado | Acepta el mejor clip libre |
| 2 | Sin etiquetas de ambiente en el lote | Los tramos exigentes quedan como huecos |
| 3 | Menos clips que tramos | Se llenan los que se pueda; el resto son huecos |
| 4 | Lote vacío | Guion entero en huecos; no es un error |
| 5 | Guion con un tramo repetido | `ValueError` al construir |

---

## 3. Componentes

| Componente | Cambio | Verificado |
|---|---|---|
| `src/media_optimizer/video/templates.py` | nuevo | ✅ |
| `profiles/hospedaje/reel_template.json` | nuevo | ✅ |
| `tests/video/test_templates.py` | nuevo | ✅ |

### 3.1 Reutilizables
| Componente | ¿Reutilizar? | Justificación |
|---|---|---|
| `ranking.RankedAsset` (HU-070) | **Sí** | Los candidatos llegan ya ordenados por calidad; el reparto no vuelve a puntuar |
| `core.errors.InvalidInputError` | Sí | Un guion mal escrito es dato del usuario, no un fallo del programa |

---

## 4. Modelo de datos

```
ReelTemplate(name, slots)              el guion, sin saber de ningún lote
  └── NarrativeSlot(name, duration_seconds, setting)

Timeline(template_name, assignments)   el guion poblado
  └── SlotAssignment(slot, asset|None) → .gaps = qué falta grabar
```

**El reparto recibe las etiquetas de ambiente como un mapping aparte**, no dentro del asset:
así `ranking/` no necesita saber de ambientes y el acoplamiento no crece.

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|-------|--------|-------------|
| RN-1 | Criterio del cliente = datos | charter §3 | Cero nombres de tramo o ambiente en el código |
| RN-2 | Determinismo | charter §6.1 | Mismo lote y guion ⇒ mismo reparto |
| RN-3 | Fail fast en contrato, fail safe en datos | `python.md` | `ValueError` al construir; `InvalidInputError` al cargar |
| RN-4 | Cobertura ≥80% del módulo | Pre-Flight | Evidencia al cierre |

---

## 6. Criterios de aceptación en BDD

### CA-1 · El guion sirve para cualquier negocio
```gherkin
DADO QUE un hospedaje abre con la fachada y un bar con la barra
CUANDO  se escribe un guion para una vertical completamente distinta
ENTONCES la plantilla lo admite sin que se modifique una sola línea del programa
```

### CA-2 · La plantilla es reutilizable entre lotes
```gherkin
DADO QUE el mismo negocio produce muchos lotes a lo largo del tiempo
CUANDO  se reparte el mismo guion sobre dos lotes distintos
ENTONCES cada reparto usa solo los clips de su lote, y la plantilla no conserva
         nada del anterior
```

### CA-3 · Falta de material produce huecos, no relleno
```gherkin
DADO QUE saber qué falta grabar es más útil que un reel que miente
CUANDO  el lote no cubre todos los ambientes que el guion espera
ENTONCES los tramos sin material quedan vacíos, el guion se declara incompleto,
         y la lista de huecos nombra exactamente los tramos que faltan
```

### CA-4 · El reparto es determinista y no repite clips
```gherkin
DADO QUE el pipeline promete la misma salida ante la misma entrada
CUANDO  se reparte el mismo guion sobre el mismo lote dos veces
ENTONCES ambos repartos son idénticos, y ningún clip aparece en dos tramos
```

### CA-5 · Un guion mal escrito se explica en vez de reventar
```gherkin
DADO QUE el guion lo escribe una persona en el archivo del perfil
CUANDO  le falta un campo o trae una duración imposible
ENTONCES falla con un mensaje que dice qué corregir, no con una traza
```

### CA-6 · El guion real del perfil es válido
```gherkin
DADO QUE el guion de ejemplo debe demostrar que la forma admite un caso real
CUANDO  se carga el archivo del perfil hospedaje
ENTONCES tiene seis tramos y suma diecinueve segundos
```

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|----------|-------------------|
| A-1 | Las etiquetas de ambiente llegan como mapping aparte | Cambiar una firma |
| A-2 | Un tramo se llena con un solo clip | Cambiar `SlotAssignment` a una tupla, aditivo |
| A-3 | El orden de los tramos lo fija el perfil, no un algoritmo | Ninguno: es la premisa |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R-1 | Que alguien escriba nombres de tramo en el código | media | **alto** (rompe charter §3) | Test que construye un guion de otra vertical |
| R-2 | Que los huecos se rellenen "por comodidad" | media | alto | 4 tests que fijan el comportamiento |
| R-3 | Que el guion quede inservible sin HU-032 | alta | bajo | Es el estado esperado y está probado |

---

## 9. Confianza global

- **Preguntas abiertas:** 0 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] Charter §3 leído; el test de otra vertical lo verifica
  - [x] `RankedAsset` leído en código: trae score, veredicto y hash
  - [x] Consumidores (HU-105, HU-072, HU-033) revisados en el backlog
- **Recomendación:** ✅ **LISTA PARA DEV. Confianza 90%.** El 10% es A-2.

---

## 10. Dependencias
| ID | Relación | Estado |
|----|----------|--------|
| HU-070 | `RankedAsset` | DONE |
| HU-132 | Datos reales del guion | backlog |
| HU-105, HU-072, HU-033 | La consumirán | backlog |

---

## 11. Historial de cambios
| Fecha | Cambio | Por |
|-------|--------|-----|
| 2026-09-05 | Creación **retroactiva** tras la auditoría de gobernanza | Claude (ejecutor) |
