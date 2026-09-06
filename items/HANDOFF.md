# HANDOFF — estado del proyecto

> Actualizado: 2026-09-06, al cerrar HU-102.
> Este archivo se reescribe al cerrar cada bloque. Dice **dónde está el proyecto** y
> **qué se puede empezar mañana sin releer nada**.

---

## 1. Estado de `develop`

| | |
|---|---|
| Commit | **`44941a7`** — *Merge branch 'feature/HU-102-score-escenas' into develop* |
| Hash completo | `44941a72958d7690de916c0df6730c55d640ca62` |
| Árbol de trabajo | limpio · pusheado |
| HUs cerradas | **58** |
| Tests | **752 passed · 1 skipped** (el omitido es comportamiento POSIX en Windows) |
| Cobertura | **99%** global · 100% en `core/` y `ranking/` |
| `ruff check` · `ruff format --check` · `mypy src/` | los tres en verde |

### Entorno

- **ffmpeg 9.0.1** instalado en `C:\ffmpeg\ffmpeg-9.0.1-essentials_build\bin`.
  Una sesión de terminal abierta antes de la instalación no lo ve: hace falta
  `export PATH="$PATH:/c/ffmpeg/ffmpeg-9.0.1-essentials_build/bin"` o una terminal nueva.
  Sin él, los tests de video se omiten en vez de fallar.
- `scenedetect 0.7.1` con un **override obligatorio** en `pyproject.toml` que deja fuera
  `opencv-python`: instala el mismo módulo `cv2` que la variante sin interfaz de ADR-002 y
  los dos se pisan. Medido: deja `cv2` inservible. **No quitar ese override.**

---

## 2. Contratos y puertos disponibles

### `core/` — dominio puro, sin IO

| Contrato | Qué representa | HU |
|---|---|---|
| `MediaAsset` · `MediaType` · `Orientation` | Ficha técnica de una foto o video | 157 |
| `QualityReport` · `Verdict` | Boleta de calidad y veredicto | 158 |
| `Transform` · `TransformHistory` · `ParamValue` | Retoques y su historial auditable | 159 |
| `BusinessProfile` · `OutputFormat` · `OutputIntent` · `ScoringWeights` | El criterio del negocio como datos | 160 |
| `StageReport` · `ReproducibleStageSummary` | Observabilidad, con lo medible separado de lo reproducible | 168 |
| `Scene` | Un tramo de video entre dos cortes | 101 |
| **`SceneScore`** | **Calificación de una escena: componentes + nota general** | **102** |
| `MediaOptimizerError` · `CorruptMediaError` · `InvalidInputError` | Jerarquía de fallos | 161 |
| `stable_text` · `stable_order` · `stable_order_by` · `stable_unique` | Determinismo | 169 |

### `core/ports/` — puertos

| Puerto | Contrato | Implementación |
|---|---|---|
| `SceneDetectorPort` | `detect(video, *, threshold) -> tuple[Scene, ...]` | `video.PySceneDetectAdapter` |

### `video/`

`PySceneDetectAdapter` · `score_scene` / `score_scenes` · `frame_to_vertical` /
`vertical_filter_chain` · `ReelTemplate` / `NarrativeSlot` / `Timeline` / `assign_slots` ·
`build_command` / `probe_filtergraph` / `run` / `degrade` / `detect_version`

### `ranking/`

`RankedAsset` · `global_score` · `rank` · `cover_candidates` · `gallery_order` ·
`select_by_format`

### CLI ejecutable hoy

```
run ingest <carpeta> · run analyze · run develop · run select · run all
report inventory · report analysis · report develop · report selection
```

---

## 3. Siguiente HU lista para DEV: **HU-103**

> `HU-103 | Descarte de escenas malas con causas | depende de HU-102 | P2 | S`

**Dependencia satisfecha:** HU-102 está DONE y expone `SceneScore` con sus componentes por
separado, que es exactamente lo que hace falta para explicar *por qué* se descarta una escena
—no basta con la nota general—.

**Punto de partida sugerido:** un veredicto por escena análogo a `Verdict` de las fotos, con
las causas derivadas de qué componente cayó bajo su umbral. Los umbrales llegan del perfil.

**Lo que HU-103 hereda y conviene leer antes:**

- La estabilidad sobre material real llega solo a **0.404** como máximo (19 escenas de los 7
  videos del cliente). La métrica **discrimina** —10 valores distintos— pero su escala es
  estricta para video de celular a pulso. Un umbral de descarte fijado a ojo dejaría fuera
  casi todo. Está anotado para HU-133, que es quien calibra.
- La nota general promedia **solo los componentes disponibles**. Cuando entre la nitidez
  (HU-023), el promedio cambia de valor sin cambiar de contrato: un umbral absoluto sobre
  `overall` se comportará distinto ese día.

---

## 4. Bloqueos y deuda declarada

| # | Qué | Impacto |
|---|---|---|
| **B-1** | **HU-023 (`ADR` de métrica de nitidez) no iniciada**, y el backlog **no la declara como dependencia de HU-102** aunque su enunciado pida nitidez | La nitidez quedó fuera de HU-102. Inconsistencia del backlog, anotada sin resolver |
| **B-2** | HU-100 (ingesta de clips con streaming) no iniciada | HU-102 muestrea cuadros por su cuenta. Cuando HU-100 llegue, conviene revisar si el muestreo debe pasar por ella |
| D-1 | `core/ports/` tiene un solo puerto y una sola implementación | Si al llegar HU-105 no aporta desacoplamiento real, el puerto cabe en `core/scene.py` y mover el archivo es todo el cambio |
| D-2 | `video/scene_scoring.py` al 98% | La línea sin cubrir es el caso en que ningún cuadro tiene contiguo — inalcanzable con clips válidos |
| D-3 | Umbral de detección de escenas en 27.0 (valor de referencia de la librería) | Sobre el video largo del cliente produce 5 escenas de menos de 1,5 s, que probablemente son paneo y no cortes. Con 40 desaparecen. Calibración: HU-133 |

---

## 5. Cómo retomar

```bash
git checkout develop && git pull
export PATH="$PATH:/c/ffmpeg/ffmpeg-9.0.1-essentials_build/bin"
uv sync
uv run pytest            # 752 passed, 1 skipped
uv run ruff check . && uv run mypy src/
```

Validar con material real (7 videos del cliente, fuera del repo):

```bash
uv run python scripts/probar_escenas_insumos.py "D:/Proyectos/Bacano (Parcela)/Living/Fotos/cell"
```

**Los medios del cliente nunca entran al repo** (charter §6.6). `.gitignore` excluye
`items/**/insumos/*.{mp4,mov,mkv,avi}`; verificado que ningún video existe en el historial.
