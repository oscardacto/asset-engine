# Insumo — HU-168 en el backlog

> Copia literal de `docs/blueprint/backlog.md`, épica **E7 · Plataforma**.

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-168 | Contrato `StageReport`: tiempo, memoria pico, transformaciones, scores por etapa | HU-150 | P0 | S |

## El mandato que materializa

CLAUDE.md, convenciones críticas transversales:

> **Observabilidad como contrato:** cada etapa del pipeline reporta tiempo, memoria pico,
> transformaciones aplicadas y scores — **no es opcional**.

Los cuatro campos del contrato son exactamente esos cuatro. No es una lista de deseos: es
el enunciado, y el alcance de esta HU es implementarlo sin añadirle nada.

## El principio con el que choca

Charter §6.1:

> **Local y determinista** — misma entrada + mismo perfil ⇒ misma salida, **byte a byte**
> donde el formato lo permita.

Y el KPI §7: *"Reproducibilidad 100% — verificado en CI con golden tests"*.

**Dos de los cuatro campos obligatorios (tiempo y memoria pico) son irreproducibles por
naturaleza.** Medir la misma etapa dos veces da números distintos en la misma máquina. Esa
tensión es el problema de diseño de esta HU, no un detalle.

## Consumidores declarados

| ID | HU | Qué le pide |
|----|----|-------------|
| HU-180 | Orquestador de etapas: un asset que falla degrada, el lote continúa | Un reporte por etapa para el resumen del run |
| HU-183 | Métricas de run en JSONL (tiempos, memoria, conteos) para auditoría histórica | Serializar el reporte |
| HU-165 | Framework de benchmarks con presupuestos por etapa | Comparar el tiempo medido contra su presupuesto |
| HU-181 | Reporte consolidado del run en Markdown | La parte legible |
