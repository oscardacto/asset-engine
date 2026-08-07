# Spec Técnica `HU-029` (+030) — `Score de exposición y veredicto técnico`

> **Estado:** LISTA PARA DEV · **Fecha:** 2026-08-06 · **Confianza:** 90%

## 1. Resumen
- HU-029: score de exposición compuesto [0,1] — fórmula parametrizada por el perfil.
- HU-030: veredicto publicable/apoyo/descartar con causas, umbrales del perfil.
- **Módulo:** `photo/analysis.py` — dominio de análisis fotográfico, puro (recibe métricas
  ya medidas + umbrales del perfil; no decodifica).
- **No obvio:** el score castiga la *distancia* al objetivo de brillo del perfil, no el
  brillo absoluto — "más brillante" no es "mejor" (una foto quemada es peor que una
  correcta). Penalizaciones de negro y quemado son restas ponderadas acotadas a [0,1].

## 2. Alcance
- IN: `ExposureThresholds` (dataclass de umbrales que HU-133 poblará desde el perfil),
  `exposure_score(metrics, thresholds)`, `verdict_for(score, flags, thresholds)` con causas.
- OUT: medir (vision/, ya hecho) · persistir (HU-035) · pesos por intención (HU-070/134).

## 5. Reglas
- Umbrales/pesos = datos (charter §3): todo llega en `ExposureThresholds`.
- Fail fast: umbrales incoherentes (objetivo fuera de [0,255], pesos negativos) ⇒ ValueError.
- Determinismo exacto.

## 11. CA
- CA-1 Score 1.0 en el objetivo exacto sin defectos; decrece monótono con la distancia.
- CA-2 Negro y quemado restan según su peso; score acotado [0,1].
- CA-3 Veredicto por umbrales del perfil, con causas legibles (qué lo bajó).
- CA-4 Flag whatsapp fuerza como máximo "apoyo" (material degradado no es publicable).
- CA-5 Umbrales incoherentes ⇒ ValueError; determinismo; cobertura ≥95% (dominio).
