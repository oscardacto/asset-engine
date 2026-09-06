# HU-135 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/video/templates.py` | `NarrativeSlot`, `ReelTemplate`, `SlotAssignment`, `Timeline`, `template_from_data`, `assign_slots` |
| `profiles/hospedaje/reel_template.json` | El guion del cliente 0 como datos: 6 tramos, 19 s |
| `tests/video/test_templates.py` | 22 tests: guion como datos, guiones inválidos, reparto, determinismo |

**Los tramos no son un enumerado del programa.** Es la decisión que sostiene toda la HU: un
hospedaje abre con la fachada y un bar con la barra, así que los nombres son texto libre del
perfil. Hay un test que construye un guion de bar nocturno completo sin tocar una línea de
código — es la prueba de que la regla se cumple, no de que se enunció.

**Cuando falta material, el hueco se conserva.** Rellenar con los mejores clips disponibles
produciría un reel completo que miente sobre la cobertura; dejar el hueco produce un reel
más corto y `Timeline.gaps`, que nombra exactamente los tramos que faltan. Ese dato es el
entregable de HU-033: qué falta grabar.

**Las etiquetas de ambiente llegan como un mapping aparte**, no dentro del asset. Así
`ranking/` no necesita saber que existen los ambientes, y cuando HU-032 produzca el
etiquetado bastará con pasarlo — sin tocar el reparto ni el contrato de `RankedAsset`.

**Estado real hoy:** sin etiquetado de ambientes (HU-032 no existe), todo tramo que exige un
ambiente queda como hueco. Es el comportamiento esperado y está cubierto por dos tests: la
HU no finge que el guion funciona más de lo que puede.

Evidencia DEV: **22 tests · `templates.py` 100%** · ruff y mypy limpios.
