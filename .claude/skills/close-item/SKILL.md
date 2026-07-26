---
name: close-item
description: >-
  Cierra un WorkItem al terminar DEV: documenta la evidencia de pruebas contra los
  criterios de aceptación de la spec y escribe closure/feedback.md +
  closure/entregables.md. Úsalo cuando el usuario dice "cierra el item ABC-123", "genera
  las evidencias de ABC-123", "documenta las pruebas de X". No aprueba el PR ni
  despliega — eso es manual y del equipo técnico.
---

# Skill: close-item

Cierra la fase QA/DONE de un WorkItem que ya pasó por `/new-item` y tiene código en
`items/<ID>/dev/`.

## Regla de oro

> `closure/feedback.md` se escribe **siempre** al cerrar, aunque el WorkItem haya ido
> limpio — es la única forma de que la siguiente sesión herede lecciones sin releer todo
> el historial.

## Pasos

1. **Leer la spec** (`items/<ID>/spec/spec_tecnica.md`) — en particular la sección de
   criterios de aceptación (§11).
2. **Probar contra los criterios de aceptación, no solo contra hallazgos de revisión de
   código.** Si un criterio nombra un dato/producto/caso exacto, probar con ESE caso —
   no uno equivalente que "debería" comportarse igual.
3. **Documentar cada criterio probado** en `closure/entregables.md`: qué se probó, con
   qué input, qué resultado dio, evidencia (log, captura, respuesta de API).
4. **Escribir `closure/feedback.md`** con, como mínimo:
   - Anti-patrones detectados (qué no volver a hacer)
   - Decisiones rechazadas (opciones evaluadas y descartadas, con justificación)
   - Lecciones aprendidas (qué mejorar en próximos WorkItems)
5. **Actualizar `ESTADO.md`** a `QA` (evidencia lista para handoff) — el paso a `DONE`
   ocurre cuando el PR se mergea, que es manual.
6. **Recordar al usuario** que el merge/deploy final requiere aprobación humana — este
   skill no lo hace.

## Plantilla de `closure/entregables.md`

```markdown
# Entregables — <ID>

## PRs mergeados
| PR # | Repositorio | Rama | Descripción |
|------|-------------|------|-------------|

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|

## Evidencia de pruebas (contra criterios de aceptación de la spec)
| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|

## Commits relevantes
<!-- Hash + descripción del commit principal -->
```

## Plantilla de `closure/feedback.md`

```markdown
# Feedback — <ID>

## Anti-patrones detectados
<!-- Qué no volver a hacer -->

## Decisiones rechazadas
<!-- Opciones evaluadas y descartadas, con justificación -->

## Lecciones aprendidas
<!-- Qué mejorar en próximos WorkItems -->
```

> Si tu proyecto necesita un entregable formal (`.docx`/PDF) para handoff a un equipo de
> QA separado, el patrón de referencia (generador OOXML vía script, sin dependencias
> externas) vive en `ClaudeCore SBS` (`.claude/skills/evidencias-hu/`) — es portable pero
> no se copió aquí para mantener este template liviano; tráelo solo si de verdad lo necesitas.
