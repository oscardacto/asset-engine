---
name: new-item
description: >-
  Conduce el desarrollo de un WorkItem por sus 3 primeras fases del ciclo de vida:
  DRAFT -> SPEC -> DEV. Úsalo cuando el usuario arranca o avanza un WorkItem por estas
  fases. Dispara con frases como "arranca el item ABC-123", "genera la spec de ABC-123",
  "indexa los insumos de ABC-123" o "pasa a dev el item X". Gobierna la carpeta
  items/<ID>/ (ESTADO.md, insumos/INDICE.md, spec/spec_tecnica.md, dev/) y custodia el
  GATE DURO de spec (0 preguntas bloqueantes + confianza >= 85%) antes de permitir
  cualquier código de desarrollo. QA y DONE quedan FUERA de alcance (los cubre
  /close-item).
---

# Skill: new-item

Este skill conduce un WorkItem por las **3 primeras fases** de su ciclo de vida:

```
DRAFT  ->  SPEC  ->  DEV        (cubierto por new-item)
              |
              v
            QA  ->  DONE         (FUERA de alcance — lo cubre /close-item)
```

> **QA y DONE están FUERA del alcance de new-item.** El cierre (`closure/feedback.md`,
> `closure/entregables.md`, merge a la rama principal) lo cubre el skill **`close-item`**.
> new-item **no toca `closure/`**.

## REGLA DE ORO

> **new-item NO escribe código de DEV si la spec no pasó el gate: 0 preguntas
> bloqueantes + confianza >= 85%** (sección de confianza de la spec). Si el gate no se
> cumple, el WorkItem se queda en **SPEC**, se listan los bloqueantes y se entregan las
> preguntas para refinamiento. Nunca se codea sobre asunción no declarada.

## Tabla de gates

| Transición | Gate de entrada | Artefacto que lo evidencia |
|---|---|---|
| (inicio) -> **DRAFT** | Insumos recibidos en `insumos/` | `ESTADO.md` + `insumos/INDICE.md` |
| **DRAFT -> SPEC** | Insumos indexados | `spec/spec_tecnica.md` generada |
| **SPEC -> DEV** | **GATE DURO: 0 bloqueantes + confianza >= 85%** | artefactos en `dev/` |
| DEV -> QA | (FUERA DE ALCANCE) | evidencia de pruebas — ver `/close-item` |
| QA -> DONE | (FUERA DE ALCANCE) | `closure/feedback.md` + `entregables.md` |

## Estructura de carpeta por WorkItem (obligatoria)

El nombre de la carpeta **debe coincidir exactamente** con el identificador del ticket.

```
items/<ID>/
├── ESTADO.md              ← estado + fecha + responsable
├── insumos/
│   └── INDICE.md          ← qué es cada archivo y por qué importa (read-only mental)
├── spec/
│   └── spec_tecnica.md    ← ver plantilla; incluye la sección de confianza (el gate)
├── dev/                    ← artefactos de desarrollo reales (código, migraciones, config)
└── closure/                ← new-item NO LO TOCA
```

Plantilla base a reutilizar: `.claude/skills/new-item/templates/spec_template.md`.
Esqueleto de carpeta: `items/_template/`.

---

## FASE 1 — DRAFT

**Objetivo:** ingestar e indexar los insumos para que la spec nazca sin ambigüedades.

### Pasos
1. **Crear/normalizar la carpeta** `items/<ID>/` clonando `items/_template/` si aún no
   existe. Verificar que el nombre coincide con el ticket.
2. **Detectar si `items/<ID>/ESTADO.md` ya existe.** Si existe con estado `DRAFT`, `SPEC`
   o `DEV` (no vacío, no `DONE`), la solicitud es **continuación de ese WorkItem** — sin
   importar que la frase del usuario suene a bug nuevo. Un bug encontrado durante las
   propias pruebas de DEV de un WorkItem sigue siendo trabajo de este WorkItem.
3. **Leer todos los insumos** en `insumos/` (HU/ticket, transcripciones de refinamiento,
   ejemplos, referencias técnicas). Si hay documentos binarios (`.docx`/`.xlsx`/`.pptx`),
   conviértelos a un formato legible antes de leerlos (no asumas contenido de un binario
   sin abrirlo).
4. **Escribir `ESTADO.md`**: `DRAFT — <YYYY-MM-DD> — @<responsable>`, y registrar el
   evento `draft` en el gate-log (ver sección **Gate-log** al final).
5. **Escribir/actualizar `insumos/INDICE.md`** con una fila por archivo (qué es y por qué
   importa).

### Gate de salida (DRAFT -> SPEC)
- Todos los insumos están **indexados** en `INDICE.md`.
- Si falta el insumo base (el ticket/HU original), **no se avanza**: se solicita.

---

## FASE 2 — SPEC

**Objetivo:** producir el análisis previo al código y **calcular la confianza**. La spec
es el contrato; mientras tenga preguntas bloqueantes, no se arranca DEV.

### Pasos
1. **Copiar la plantilla** a `items/<ID>/spec/spec_tecnica.md`.
2. **Llenar resumen, alcance (IN/OUT), componentes técnicos y modelo de datos** — cada
   regla de negocio con **fuente exacta** (sección del ticket, minuto del audio, fila del
   Excel). Las "aclaraciones" del ticket se **promueven** a reglas de negocio explícitas.
3. **Verificar el esquema real** contra el sistema real (BD/API vía MCP o equivalente,
   solo lectura) antes de asumir nombres de columnas/campos/endpoints. Marcar cada
   suposición como **verificada** o **asumida** — lo asumido genera pregunta.
4. **Completar preguntas abiertas** con: texto literal, categoría (BLOQUEANTE /
   IMPORTANTE / INFORMATIVA), dueño, por qué importa, mejor hipótesis, costo si se asume
   mal, origen.
5. **Completar asunciones explícitas** — lo que se asumirá si la pregunta no se responde,
   con su costo si se rompe.
6. **Calcular la confianza global:**
   - Contar preguntas abiertas totales y **bloqueantes**.
   - Marcar las verificaciones cruzadas hechas (codebase actual, esquema real, componentes
     reutilizables buscados no asumidos).
   - Emitir recomendación: LISTA PARA DEV / REQUIERE REFINAMIENTO / NO VIABLE.

### Gate de salida (SPEC -> DEV) — GATE DURO
| Condición | Umbral |
|---|---|
| Preguntas **BLOQUEANTES** abiertas | **= 0** |
| Confianza global | **>= 85%** |

- **Si SE cumple:** marcar la spec como `LISTA PARA DEV`, actualizar `ESTADO.md` y
  proceder a FASE 3.
- **Si NO se cumple:** el WorkItem **se queda en SPEC**. Entregar la lista de bloqueantes
  y preguntas para la sesión de refinamiento. **No se inicia `dev/`** (REGLA DE ORO).
- **En AMBOS casos:** registrar el evento `gate_spec` en el gate-log con la confianza,
  el conteo de preguntas y el resultado (ver sección **Gate-log**). Cada re-evaluación
  tras un refinamiento se registra como un intento nuevo — nunca se sobreescribe.

---

## FASE 3 — DEV

**Objetivo:** generar los artefactos de desarrollo, **solo** si el gate de spec pasó.

> **Precondición innegociable:** la spec está en `LISTA PARA DEV` (0 bloqueantes +
> confianza >= 85%). Sin esto, new-item se detiene aquí.

### Pasos
1. **Re-verificar el gate** leyendo la spec. Si no está en `LISTA PARA DEV`, abortar y
   regresar a FASE 2.
2. **Buscar componentes reutilizables existentes** antes de crear nuevos — no dupliques
   lógica ya presente en el codebase.
3. **Migraciones/artefactos versionados** (si aplica): idempotentes (tolerar doble
   ejecución), verificados contra el esquema real antes de darlos por buenos.
4. **Código backend/frontend** según convenciones reales del proyecto (ver `CLAUDE.md` y
   `.claude/rules/`).
5. **Actualizar la spec** con lo realmente construido. Si en DEV aparece un caso nuevo o
   una contradicción, **se actualiza la spec primero** y, si reabre un bloqueante, se
   regresa a SPEC.
6. **Pruebas de DEV con prioridad clara:** primero los criterios de aceptación de la spec,
   sin excepción; los casos exhaustivos adicionales (partición de equivalencia, boundary
   values) son una **capa secundaria**, etiquetada como tal — nunca se presentan mezclados
   con la cobertura de criterios de aceptación como si fueran lo mismo.
7. **Actualizar `ESTADO.md`** a `DEV` y registrar el evento `dev` en el gate-log.

### Gate de salida (DEV -> QA)
> **FUERA DE ALCANCE de new-item** — el siguiente paso concreto es invocar `/close-item`
> para producir la evidencia de pruebas y entregar a QA. Recordar explícitamente este
> siguiente paso al usuario al terminar la FASE 3, no darlo por hecho.

---

## Gate-log — memoria estructurada del gate

Cada evento del ciclo se registra como **una línea JSON** al final de
`items/_metrics/gate-log.jsonl` (crear el archivo si no existe; **append-only**, nunca
reescribirlo). Esto convierte "pasó el gate" de una frase en un `.md` a un dato
consultable: con el tiempo permite medir si la confianza declarada (85%, 92%…) predice
el resultado real en QA, y cuánto tarda DRAFT→DEV.

Eventos que escribe new-item:

```json
{"item":"HU-021","evento":"draft","fecha":"2026-07-26"}
{"item":"HU-021","evento":"gate_spec","fecha":"2026-07-27","intento":1,"confianza":78,"bloqueantes":2,"importantes":3,"informativas":1,"resultado":"REQUIERE_REFINAMIENTO"}
{"item":"HU-021","evento":"gate_spec","fecha":"2026-07-28","intento":2,"confianza":91,"bloqueantes":0,"importantes":1,"informativas":2,"resultado":"LISTA_PARA_DEV"}
{"item":"HU-021","evento":"dev","fecha":"2026-07-28"}
```

Los eventos `qa` y `done` los escribe `/close-item`. Esquema completo y consultas de
ejemplo: `items/_metrics/README.md`.
