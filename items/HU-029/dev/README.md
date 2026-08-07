# HU-029 (+030+035+036+037) — Artefactos de DEV

| Artefacto | Qué es | HU |
|---|---|-----|
| `photo/analysis.py` | `ExposureThresholds` + `exposure_score` + `verdict_for` con causas | 029, 030 |
| `pipeline/stages.py` (`_analyze`) | Etapa: catálogo → métricas + flags + veredicto por foto → `analysis.json` determinista | 035, 037 |
| `pipeline/reports.py` (`_analysis`) | Tabla ordenada por score con veredicto, flags y causas | 036 |
| `tests/photo/` + ampliaciones | 15 + 7 tests | — |

**El score castiga distancia al objetivo, no premia brillo** — una foto quemada es peor que
una correcta. WhatsApp nunca es publicable: la calidad perdida no se recupera (con test).

**Rework de HU-020 (registrado):** `luminance` casteaba la imagen completa a float64 — en
las fotos de 200 MP del lote real son ~4.8 GB temporales por foto y la etapa se colgaba.
Sustituido por `cvtColor` de OpenCV (mismos pesos Rec. 601, en C): la etapa pasó de >2 min
colgada a **38 s por las 102 fotos**. Los tests de colores puros siguen fijando los
coeficientes.

**Los umbrales del cliente 0 viven como datos con `TODO(HU-131)`**: pasan al perfil cuando
exista su carga; la fórmula ya solo sabe restar.

**Validación real:** 86 fotos analizadas → 38 publicables · 38 apoyo · 10 descartes; las 16
WA capadas a apoyo con su causa; `analysis.json` byte-idéntico entre corridas.

Evidencia: **561 tests (22 nuevos) · ruff y mypy limpios**.
