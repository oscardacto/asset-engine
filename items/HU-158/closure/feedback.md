# Feedback — HU-158

## Anti-patrones detectados
- (Ninguno nuevo — la HU aplicó desde el arranque las dos correcciones heredadas:
  docstrings sin proceso y clases de test nombradas por comportamiento, no por "CA-N".)

## Decisiones rechazadas
- **Campos tipados por métrica** (`brightness: float`, `sharpness: float`…) — rechazado:
  cada HU de análisis nueva rompería el contrato; el conjunto de métricas es abierto y
  el mapping lo absorbe sin churn.
- **Referencia al `MediaAsset` dentro del reporte** — rechazado (A-1): el catálogo asocia
  asset↔reporte; añadir la referencia después es aditivo.
- **Veredicto opcional** (`Verdict | None`) — rechazado (A-2): un "reporte a medias" es un
  intermedio interno de la etapa de análisis, no un estado del dominio.
- **Compartir la referencia del dict del llamador** — rechazado: copia defensiva a mapping
  de solo lectura; el aliasing habría sido un bug silencioso de determinismo.

## Lecciones aprendidas
- **NaN es el enemigo silencioso del determinismo:** `NaN != NaN` rompe igualdad de
  reportes y comparaciones de umbral sin lanzar error. Rechazarlo en construcción convierte
  un bug intermitente futuro en un fail-fast inmediato. Aplicar el mismo criterio en
  cualquier contrato futuro que transporte floats.
- **Conjunto abierto ⇒ mapping/set; conjunto cerrado ⇒ enum.** La distinción (métricas y
  flags crecen, el veredicto no) salió directa del inventario de HUs consumidoras en el
  insumo — hacer ese inventario antes de diseñar evitó el debate en DEV.
- **`field(hash=False)` sobre el mapping** mantiene el reporte hashable sin violar el
  contrato igualdad⇒hash — patrón útil para contratos con colecciones no hashables.
