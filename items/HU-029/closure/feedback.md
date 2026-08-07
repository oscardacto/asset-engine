# Feedback — HU-029+030+035+036+037

## Rework (contra HU-020)
`luminance` con cast a float64 completo: correcto en fixtures de 64px, inviable en las
fotos de 200 MP del lote real (~4.8 GB temporales; la etapa se colgaba). Causa raíz:
**los tests sintéticos no ejercitan la escala real** — el defecto solo apareció al correr
la etapa sobre el lote del cliente. `cvtColor` da los mismos pesos en C: >2 min → 38 s.
Lección: toda métrica nueva se valida contra el lote real antes de cerrar, no solo contra
fixtures — el benchmark formal llega con HU-165.

## Decisiones
- Análisis en `analysis.json` junto al catálogo (misma familia de manifiestos ADR-003),
  clave por hash de contenido: sobrevive renombres (HU-013).
- Foto que no decodifica → se cuenta como ilegible y la etapa termina PARTIAL; no tumba.
- Umbrales del cliente 0 como datos con `TODO(HU-131)` — la única deuda declarada.
