# HU-168 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/core/stage_report.py` | `StageReport` + `ReproducibleStageSummary` |
| `src/media_optimizer/core/__init__.py` | Exporta ambos |
| `tests/core/test_stage_report.py` | 25 tests: los cuatro campos, separación de lo medido, valores imposibles, determinismo |

**El contrato traía su propia contradicción.** CLAUDE.md exige que toda etapa reporte
tiempo y memoria pico; el charter promete que la misma entrada da la misma salida byte a
byte, y hay golden tests que lo comprueban. Dos de los cuatro campos obligatorios son
irreproducibles por naturaleza.

**Cómo se resolvió:** lo comparable vive en un **tipo distinto**, `ReproducibleStageSummary`
(etapa + transformaciones + scores). Un `StageReport` completo no puede colarse en una
comparación de reproducibilidad porque no encaja — lo impide el verificador de tipos, no la
memoria de quien escribe el test. Sin esa separación, un golden test fallaría de vez en
cuando mostrando `0.031` contra `0.029`, que parece ruido y no un defecto de diseño.

**La separación se probó en las dos direcciones**, que es lo que la hace confiable: dos
reportes con tiempos y memorias muy distintos comparan **iguales**, y dos reportes que
difieren en lo que la etapa realmente hizo comparan **distinto**. Solo el primer test
dejaría pasar una implementación que devolviera siempre lo mismo.

**Aquí no se mide nada.** Medir es impuro y le toca a la capa que orquesta (HU-180); este
módulo recibe lo ya medido. Los conteos del run son de HU-183, no de este contrato: el
mandato son cuatro campos y se implementaron cuatro.

Evidencia DEV: **379 tests passed (25 nuevos) · `stage_report.py` 100%** · ruff y mypy limpios.
