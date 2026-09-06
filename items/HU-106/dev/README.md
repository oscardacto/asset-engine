# HU-106 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `core/scene_trimmer.py` | `TrimStrategy`, `TrimPlan`, `trim_to_target`, `MINIMO_POR_ESCENA` |
| `tests/core/test_scene_trimmer.py` | 32 tests |

**La aritmética va en milisegundos enteros.** Medido antes de escribir código: el recorte
proporcional en coma flotante da 15.000000000000002 en vez de 15. El sobrante de la división
se le da a una sola escena — un milisegundo, imperceptible a 30 cuadros por segundo.

**Lo que falta no se inventa.** Material más corto que la meta se devuelve entero, con
`is_exact` en falso. Alargarlo exigiría repetir cuadros o ralentizar, que cambia lo que se
ve: es transformación de contenido, no ajuste de duración.

**El mínimo por escena evita parpadeos.** Recortar mucho convierte una toma de 1 s en un
destello inútil; esas se descartan y su tiempo se reparte entre las que quedan. El bucle de
descarte reduce el conjunto en cada vuelta, así que termina siempre.

**`is_exact` se calcula, no se guarda**: no puede existir un plan que diga que cerró y no
cierre.

Se adelantó a HU-105, su dependencia declarada, porque esa dependencia era de **orden de uso,
no de código**: el recorte opera sobre `Scene` y no necesita el guion. HU-105 sigue bloqueada
por HU-032.

Evidencia: **835 tests · `scene_trimmer.py` 100% · total 99%**.
