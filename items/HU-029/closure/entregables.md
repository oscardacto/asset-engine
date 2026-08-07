# Entregables — HU-029+030+035+036+037

| CA (spec §11) | Resultado |
|----|-----------|
| Score 1.0 en objetivo, decrece monótono ambas direcciones | ✅ 3 tests |
| Negro/quemado restan por peso; acotado [0,1] | ✅ 2 tests |
| Veredicto por umbrales con causas legibles | ✅ 3 tests |
| WhatsApp fuerza máximo "apoyo" | ✅ 2 tests (no salva descartadas) |
| Umbrales incoherentes ⇒ ValueError | ✅ 3 tests |
| `analysis.json` determinista byte a byte | ✅ test + validado en lote real |
| Etapa `analyze` y reporte `analysis` ejecutables | ✅ E2E + lote real (38 s / 102 fotos) |

**5 HUs · 0 criterios fallidos · 1 rework registrado (HU-020, rendimiento en 200 MP).**
