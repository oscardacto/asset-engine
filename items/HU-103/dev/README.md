# HU-103 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `core/scene_selection.py` | `DiscardReason`, `SceneThresholds`, `SceneVerdict`, `judge_scene`, `select_scenes`, `kept_scenes` |
| `tests/core/test_scene_selector.py` | 28 tests |

**Dominio puro**: solo `dataclasses` y `enum`, más los contratos `Scene` y `SceneScore`.
Ni ffmpeg, ni OpenCV, ni la librería de escenas.

## Las dos decisiones que vienen de los avisos del HANDOFF

**Los umbrales van por componente, nunca sobre la nota general.** HU-102 dejó anotado que esa
nota promedia solo lo medido y que cambiará de valor cuando entre la nitidez. Un umbral sobre
ella se comportaría distinto ese día sin que nadie tocara nada. Hay dos tests que fijan esta
propiedad: dos escenas con la misma nota pueden tener veredictos distintos, y una nota alta
no salva un componente hundido.

**Los umbrales por defecto salen de 19 escenas reales, no de intuición.** La estabilidad del
material del cliente llega como máximo a 0.404, así que un mínimo de 0.5 —que suena razonable
en abstracto— habría descartado el lote entero.

## `keep` es derivado, no un campo

Se deduce de si hay causas. Así **no se puede construir** una escena marcada como buena que a
la vez traiga motivos de descarte: el estado imposible no existe. Hay un test que comprueba
que `keep` no aparece entre los campos asignables.

## Validación con el material real (7 videos, 19 escenas)

```
TOTAL: 8 conservadas de 19 escenas (42%)
causas: {'too_short': 5, 'unstable': 10, 'poor_exposure': 0}
```

Ni vacía el lote ni lo deja pasar entero. Y ninguna escena se descarta por luz, que es lo
correcto: el material del cliente está bien expuesto (0.799–0.976); su problema es el pulso.

Evidencia: **28 tests · `scene_selection.py` 100% · total 99%**.
