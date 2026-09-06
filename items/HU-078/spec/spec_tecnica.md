# Spec Técnica `HU-078` (+070+071+072+074) — `Cadena select`

> **Estado:** LISTA PARA DEV · **Fecha:** 2026-08-06 · **Confianza:** 88%

## 1. Resumen
- `ranking/selection.py` (dominio puro, cobertura ≥95%): score global ponderado (070),
  candidatas a portada (071), orden de galería por plantilla-como-datos (072), selección
  por formato con elegibilidad técnica (074).
- Etapa `select` (078): analysis.json → selection.json determinista + resumen.
- **No obvio:** la plantilla narrativa por ambientes exige el etiquetado humano (HU-032) y
  los ambientes del perfil (E6), que no existen. La plantilla se implementa **como datos**
  (tupla de criterios) sobre lo disponible — gancho (mejor publicable) + alternancia de
  orientación para ritmo visual — y la de ambientes entra con HU-135 sin tocar el motor.

## CA
- CA-1 Score global = combinación ponderada por pesos (datos); determinista.
- CA-2 Portada: solo publicables elegibles para cover, top-N por score.
- CA-3 Galería: el gancho es la mejor publicable; el orden es estable y reproducible.
- CA-4 Por formato: una foto bajo el nativo de una intención queda fuera de esa intención.
- CA-5 Los descartes nunca entran en ninguna selección.
- CA-6 selection.json byte-idéntico entre corridas; `run select` y `report selection` funcionan.
- CA-7 Sin analysis ⇒ mensaje accionable. Cobertura ≥95% dominio. Gate-log 070/071/072/074/078.
