# Insumo — HU-020 (+021+022) en el backlog

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-020 | Brillo medio por asset (paridad ±2% con auditoría manual del cliente 0) | HU-158, HU-166 | P0 | S |
| HU-021 | Histograma: % de píxeles en negro aplastado (umbral por perfil) | HU-020 | P0 | S |
| HU-022 | % de altas luces quemadas | HU-020 | P0 | S |

Se desarrollan juntas: son tres lecturas del mismo histograma de luminancia, y separarlas
obligaría a decodificar la misma imagen tres veces. Cada una conserva su criterio de
aceptación propio y su cierre en el gate-log.

## KPI del charter §7
> "Las métricas de análisis reproducen las tablas del Maestro §8.2 (brillo medio, % negro)
> dentro de ±2%"

## Regla del perfil
Los umbrales (qué es "negro aplastado", qué es "quemado") son **datos del perfil**
(HU-133); estas HUs entregan las funciones puras que los reciben como parámetro.
