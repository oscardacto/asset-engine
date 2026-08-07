# Feedback — HU-018

## Lecciones aprendidas
- **La simetría etapas/reportes pagó de inmediato**: `reports.py` reusó el patrón completo
  de `stages.py` (registro + disponibilidad derivada + petición/resultado congelados) y el
  comando quedó en una llamada. Los 6 reportes restantes son ahora una función cada uno.
- **"Sin timestamp" necesita test propio**: es la clase de regresión que nadie nota hasta
  que un golden test falla 1 de cada N veces. `test_el_reporte_no_contiene_fecha_ni_hora`
  la bloquea de raíz.

## Decisiones rechazadas
- **Timestamp en el reporte** — rompería la comparación byte a byte; la fecha del run vive
  en el rastro estructurado, que no es salida comparable.
- **Implementar `jsonl` para inventory** — es el formato de las métricas de run (HU-183);
  pedirlo aquí avisa con claridad en vez de producir algo a medias.
