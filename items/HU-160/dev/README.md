# HU-160 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/core/business_profile.py` | `OutputIntent`, `OutputFormat`, `ScoringWeights`, `BusinessProfile` |
| `src/media_optimizer/core/__init__.py` | Exporta los 4 contratos nuevos |
| `tests/core/test_business_profile.py` | 52 tests: formatos, pesos, umbrales, ambientes, determinismo, inmutabilidad, **generalización** |

**La decisión de forma.** El riesgo real aquí no era un bug, era una estructura equivocada:
demasiado específica convierte el criterio de un cliente en código; demasiado genérica
(`dict[str, Any]`) no contrata nada. La línea que se aplicó no es "cuántos campos" sino
**quién conoce la respuesta**: si el nombre lo sabe el código —una intención de salida
existe porque hay una etapa que la produce— es estructura cerrada; si solo lo sabe el
negocio —qué ambientes espera, cuánto pesa la nitidez— es dato abierto. Por eso
`OutputIntent` es un enum y los ambientes son texto libre.

**El aspecto se deriva, no se declara.** Guardar `"4:5"` junto a `1080×1350` serían dos
fuentes de verdad que pueden contradecirse. Con las dimensiones basta: el aspecto es un
cálculo y el mínimo de resolución que HU-008 necesita es el propio par.

**Todo queda ordenado al construir.** No es estética: el pipeline promete que la misma
entrada da la misma salida, y recorrer un perfil en distinto orden bastaría para romperlo.

**La prueba de generalización se verificó inyectando la violación.** Se añadió al módulo un
`AMBIENTES_HOSPEDAJE = ("cocina", "alcoba")` y la prueba falló en 3 de sus casos, incluido
el que vigila el nombre del cliente. Sin esa comprobación no habría forma de saber si
pasaba por estar bien o por no mirar nada. Mira el árbol sintáctico y **descarta los textos
de documentación**: describir la regla no es violarla.

Evidencia DEV: **354 tests passed (52 nuevos) · `business_profile.py` 100%** · ruff y mypy limpios.
