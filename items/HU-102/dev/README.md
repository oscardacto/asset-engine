# HU-102 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `core/scene_score.py` | `SceneScore`: componentes medidos + nota general |
| `video/scene_scoring.py` | `score_scene` / `score_scenes`: muestreo y cálculo |
| `tests/core/test_scene_score.py` | 10 tests del contrato |
| `tests/video/test_scene_scoring.py` | 21 tests, incluidos los de degradación |

**La nitidez quedó fuera a propósito.** El enunciado la pide, pero HU-023 —el `ADR` que decide
*cómo* medirla— no está iniciada, y HU-102 ni siquiera la declara como dependencia.
Implementarla aquí habría cerrado una decisión de stack saltándose su ADR. La nota general
promedia **solo los componentes disponibles**, así que la nitidez entra después sin tocar el
contrato ni a quien lo consume.

**No se recorre el clip.** Se salta a posiciones calculadas y se leen cuadros sueltos: una
escena de treinta segundos cuesta lo mismo que una de tres. El charter prohíbe cargar video
completo a RAM.

## Defecto encontrado en material real y corregido

La primera versión comparaba las **muestras entre sí** —separadas por alrededor de un
segundo— para medir estabilidad. Sobre los 7 videos del cliente, eso dio **0.000 en casi
todas las escenas**: dos cuadros a un segundo de distancia difieren mucho aunque la cámara
esté quieta, así que la métrica no distinguía nada.

Se corrigió a comparar cada cuadro con **el inmediatamente siguiente**. Resultado sobre el
mismo material: 10 valores distintos en 19 escenas, rango 0.000–0.404. La métrica discrimina.

Era el riesgo R-4 declarado en la spec —*estabilidad confunda paneo con temblor*— y se
confirmó. Hay un test de regresión que lo fija: subir el número de muestras no puede
desplomar la estabilidad de un clip quieto.

Evidencia: **752 tests · `scene_score.py` 100% · `scene_scoring.py` 98%** (la rama sin cubrir
es el caso en que ningún cuadro tiene contiguo, inalcanzable con clips válidos).
