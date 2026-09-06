# HANDOFF — estado del proyecto

> Actualizado: 2026-09-06, al cerrar HU-106.
> Este archivo se reescribe al cerrar cada bloque. Dice **dónde está el proyecto** y
> **qué se puede empezar mañana sin releer nada**.

---

## 1. Estado de `develop`

| | |
|---|---|
| Commit | ver §7 — actualizado en el merge de HU-106 |
| Árbol de trabajo | limpio · pusheado |
| HUs cerradas | **61** |
| Tests | **835 passed · 1 skipped** (el omitido es comportamiento POSIX en Windows) |
| Cobertura | **99%** global · 100% en `core/`, `ranking/` y `video/framing.py` |
| `ruff check` · `ruff format --check` · `mypy src/` | los tres en verde |

### Entorno

- **ffmpeg 9.0.1** en `C:\ffmpeg\ffmpeg-9.0.1-essentials_build\bin`. Una terminal abierta
  antes de la instalación no lo ve: hace falta
  `export PATH="$PATH:/c/ffmpeg/ffmpeg-9.0.1-essentials_build/bin"` o una sesión nueva.
  Sin él, los tests de video se omiten en vez de fallar.
- `scenedetect 0.7.1` con un **override obligatorio** en `pyproject.toml` que deja fuera
  `opencv-python`: instala el mismo módulo `cv2` que la variante sin interfaz de ADR-002 y
  los dos se pisan. Medido: deja `cv2` inservible. **No quitar ese override.**
- Los tests pueden fallar al limpiar symlinks en `%TEMP%\pytest-of-*` por permisos. Es
  infraestructura local, no código: se esquiva con `--basetemp`.

---

## 2. Lo que se sabe del material del cliente — **léelo antes de diseñar nada de video**

Tres hechos medidos sobre los 7 videos reales, que ya cambiaron dos decisiones:

| Hecho | Medida | Consecuencia |
|---|---|---|
| **El celular graba 9:16 nativo** | 6 de 7 clips son 1080×1920; el otro, 720×1280 | **Ningún clip recorta ancho.** El encuadre solo escala. La ruta de material apaisado funciona y está probada, pero con clips sintéticos — no se ejercita con este cliente |
| **La estabilidad es baja y su escala es estrecha** | 0.000 – **0.404** en 19 escenas | Un umbral de 0.5 —permisivo en abstracto— descartaría el lote entero. El adoptado es 0.15 |
| **La exposición es buena** | 0.799 – 0.976 | Nada se descarta por luz. El problema del cliente es el pulso, no la iluminación |

**Regla que sale de aquí: ningún umbral entra sin haber visto la distribución real de la
métrica sobre la que se aplica.** Un test unitario con dos casos separados pasa igual aunque
el umbral vacíe el lote en producción.

**Y una advertencia de inversión:** antes de construir encuadre inteligente o cualquier cosa
que resuelva material horizontal, comprobar si ese material existe. Hoy no.

---

## 3. Contratos y puertos disponibles

### `core/` — dominio puro, sin IO

| Contrato | Qué representa | HU |
|---|---|---|
| `MediaAsset` · `MediaType` · `Orientation` | Ficha técnica de una foto o video | 157 |
| `QualityReport` · `Verdict` | Boleta de calidad y veredicto | 158 |
| `Transform` · `TransformHistory` · `ParamValue` | Retoques y su historial auditable | 159 |
| `BusinessProfile` · `OutputFormat` · `OutputIntent` · `ScoringWeights` | El criterio del negocio como datos | 160 |
| `StageReport` · `ReproducibleStageSummary` | Observabilidad, con lo medible separado de lo reproducible | 168 |
| `Scene` | Un tramo de video entre dos cortes | 101 |
| `SceneScore` | Calificación de una escena: componentes + nota general | 102 |
| `DiscardReason` · `SceneThresholds` · `SceneVerdict` | Qué escenas sirven y por qué no las otras | 103 |
| **`TrimStrategy` · `TrimPlan`** | **Ajuste de escenas a una duración objetivo exacta** | **106** |
| `MediaOptimizerError` · `CorruptMediaError` · `InvalidInputError` | Jerarquía de fallos | 161 |
| `stable_text` · `stable_order` · `stable_order_by` · `stable_unique` | Determinismo | 169 |

**Nuevo en `core/scene_trimmer.py`** (HU-106) — dominio puro:

```
trim_to_target(scenes, target_seconds, *, strategy, min_scene_seconds) -> TrimPlan
TrimStrategy.PROPORTIONAL   todas encogen igual: aparece todo el recorrido
TrimStrategy.DROP_TAIL      las primeras salen enteras; el resto se descarta
MINIMO_POR_ESCENA           1.0 s — evita que un recorte deje un parpadeo
```

**La cuenta va en milisegundos enteros.** En coma flotante el recorte proporcional da
15.000000000000002 en vez de 15, y el charter promete duraciones exactas. `TrimPlan.is_exact`
se calcula, no se guarda. **Material más corto que la meta no se alarga**: se devuelve entero
con `is_exact` en falso, porque repetir cuadros o ralentizar cambia lo que se ve.

### `core/ports/`

| Puerto | Contrato | Implementación |
|---|---|---|
| `SceneDetectorPort` | `detect(video, *, threshold) -> tuple[Scene, ...]` | `video.PySceneDetectAdapter` |

### `video/`

| Módulo | Qué expone |
|---|---|
| `ffmpeg_executor` | `build_command` · `probe_filtergraph` · `run` · `degrade` · `detect_version` · `is_available` |
| `transforms` | `frame_to_vertical` · `vertical_filter_chain` · `VerticalFraming` · `CropBox` |
| **`framing`** | **`read_dimensions` · `build_crop_command` · `crop_to_vertical`** |
| `scenedetect_adapter` | `PySceneDetectAdapter` |
| `scene_scoring` | `score_scene` · `score_scenes` |
| `templates` | `ReelTemplate` · `NarrativeSlot` · `Timeline` · `assign_slots` · `template_from_data` |

**Nuevo en `video/framing.py`** (HU-104):

```
read_dimensions(video)                          -> (ancho, alto)
build_crop_command(video, framing, output, *, offset_x, fps) -> tuple[str, ...]   puro
crop_to_vertical(video, output, *, offset_x, fps)            -> VerticalFraming   ejecuta
```

`crop_to_vertical` **devuelve el encuadre aplicado**, no un booleano: HU-110 necesitará
explicar qué parte del material se recortó. El desplazamiento se **acota al margen** en vez
de fallar, para que un parámetro mal puesto no interrumpa un lote a la mitad.

### `ranking/`

`RankedAsset` · `global_score` · `rank` · `cover_candidates` · `gallery_order` ·
`select_by_format`

### CLI ejecutable hoy

```
run ingest <carpeta> · run analyze · run develop · run select · run all
report inventory · report analysis · report develop · report selection
```

---

## 4. Estado de la épica E5 (video)

| HU | Qué es | Estado |
|----|--------|--------|
| 101 | Detección de escenas | ✅ DONE |
| 102 | Score técnico por escena | ✅ DONE |
| 103 | Descarte con causas | ✅ DONE |
| 104 | Crop 9:16 | ✅ DONE |
| **105** | **Secuenciado narrativo según plantilla** | **lista, con reserva — ver §5** |
| 106 | Recorte de clips a duración objetivo | ✅ DONE |
| **107** | **Ensamblado del reel con transiciones** | **lista — 106 ya está** |
| 109 | Export 1080×1920 con codec por plataforma | depende de 107 |
| 110 | CLI `run reel` + reporte de escenas | depende de 109 |
| 100 | Ingesta de clips con streaming | no iniciada — ver B-2 |

---

## 5. Siguiente HU: **HU-107** (ensamblado del reel)

Con HU-106 cerrada, el camino queda: escenas detectadas (101) → puntuadas (102) → filtradas
(103) → encuadradas (104) → **ajustadas a duración (106)** → **ensambladas (107)**.

**HU-107 es lo que produce el primer reel de verdad.** Junta clips en un solo archivo con
transiciones simples. Todo lo que necesita existe: `crop_to_vertical` para el formato,
`TrimPlan` para las duraciones, y el ejecutor con sus banderas de reproducibilidad.

**HU-105 sigue bloqueada y no por código.** `kept_scenes` y `assign_slots` ya existen y es
cablearlos, pero `assign_slots` reparte **por ambiente** y HU-032 no existe. Los 6 tramos del
guion `hospedaje` **declaran ambiente**, así que hoy la línea de tiempo saldría vacía. Hacerla
ahora daría código correcto que no puede demostrarse útil. **Si se prioriza el reel narrativo,
antes va HU-032.**

Sin HU-105, HU-107 puede ensamblar en el orden que dé el ranking en vez del guion — un reel
válido, solo que no narrativo.

---

## 6. Bloqueos y deuda declarada

| # | Qué | Impacto |
|---|---|---|
| **B-1** | **HU-023 (`ADR` de métrica de nitidez) no iniciada**, y el backlog **no la declara como dependencia de HU-102** aunque su enunciado la pida | La nitidez quedó fuera de HU-102 y de las causas de HU-103. Inconsistencia del backlog, anotada sin resolver |
| **B-2** | HU-100 (ingesta de clips con streaming) no iniciada | HU-102 muestrea cuadros y HU-104 lee dimensiones, ambos por su cuenta. Cuando HU-100 llegue, revisar si esas lecturas deben pasar por ella |
| **B-3** | HU-032 (etiquetado de ambientes) no iniciada | **Bloquea el valor de HU-105**: los 6 tramos del guion `hospedaje` declaran ambiente, así que la línea de tiempo saldría vacía |
| D-1 | `core/ports/` tiene un solo puerto y una sola implementación | Si al llegar HU-105 no aporta desacoplamiento real, el puerto cabe en `core/scene.py` |
| D-2 | `video/scene_scoring.py` al 98% | La línea sin cubrir es el caso en que ningún cuadro tiene contiguo — inalcanzable con clips válidos |
| D-3 | Umbral de detección de escenas en 27.0 | Sobre el video largo produce 5 escenas de menos de 1,5 s. Con 40 desaparecen. Calibración: HU-133 |
| D-4 | Los umbrales de descarte son un punto de partida medido, no calibrado | HU-133 los fija en el perfil. Con los actuales sobrevive el 42% (8 de 19) |
| D-5 | La salida de `crop_to_vertical` no está afinada para plataforma | Codec, bitrate y perfil de color son HU-109 |
| D-6 | `MINIMO_POR_ESCENA` (1 s) **no está calibrado con material real**, a diferencia de los umbrales de HU-103 | HU-133 debería revisarlo junto al umbral de duración de descarte (1,5 s), con el que guarda relación |

---

## 7. Cómo retomar

```bash
git checkout develop && git pull
export PATH="$PATH:/c/ffmpeg/ffmpeg-9.0.1-essentials_build/bin"
uv sync
uv run pytest            # 835 passed, 1 skipped
uv run ruff check . && uv run ruff format --check . && uv run mypy src/
```

Validar con material real (7 videos del cliente, fuera del repo):

```bash
uv run python scripts/probar_escenas_insumos.py "D:/Proyectos/Bacano (Parcela)/Living/Fotos/cell"
```

**Los medios del cliente nunca entran al repo** (charter §6.6). `.gitignore` excluye
`items/**/insumos/*.{mp4,mov,mkv,avi}`; verificado que ningún video existe en el historial.
