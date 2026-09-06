# HANDOFF — estado del proyecto

> Actualizado: 2026-09-06, al cerrar HU-103.
> Este archivo se reescribe al cerrar cada bloque. Dice **dónde está el proyecto** y
> **qué se puede empezar mañana sin releer nada**.

---

## 1. Estado de `develop`

| | |
|---|---|
| Commit | ver §6 — actualizado en el merge de HU-103 |
| Árbol de trabajo | limpio · pusheado |
| HUs cerradas | **59** |
| Tests | **780 passed · 1 skipped** (el omitido es comportamiento POSIX en Windows) |
| Cobertura | **99%** global · 100% en `core/` y `ranking/` |
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
| `SceneScore` | Calificación de una escena: componentes + nota general | 102 |
| **`DiscardReason` · `SceneThresholds` · `SceneVerdict`** | **Qué escenas sirven y por qué no las otras** | **103** |
| `MediaOptimizerError` · `CorruptMediaError` · `InvalidInputError` | Jerarquía de fallos | 161 |
| `stable_text` · `stable_order` · `stable_order_by` · `stable_unique` | Determinismo | 169 |

**Nuevo en `core/scene_selection.py`** — dominio puro, sin ffmpeg ni OpenCV:

```
judge_scene(scene, score, thresholds)   -> SceneVerdict     una escena
select_scenes(scenes, scores, thresh)   -> tuple[SceneVerdict, ...]   el lote
kept_scenes(scenes, scores, thresholds) -> tuple[Scene, ...]  solo las supervivientes
UMBRALES_POR_DEFECTO                     SceneThresholds ya calibrado con material real
```

### `core/ports/`

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

## 3. Lo aprendido sobre los umbrales de video — **léelo antes de tocar ninguno**

La escala de estabilidad **no se comporta como una escala de 0 a 1 normal** cuando el
material se graba a pulso. Sobre los 7 videos del cliente (19 escenas):

| Métrica | Rango real | Qué implica |
|---|---|---|
| **Estabilidad** | **0.000 – 0.404** | Un mínimo de 0.5 —que en abstracto suena permisivo— **descartaría las 19 escenas**. El valor adoptado es **0.15** |
| Exposición | 0.799 – 0.976 | Nada se descarta hoy por luz, y es correcto: el problema del cliente es el pulso |
| Duración | 5 escenas bajo 1,5 s | Paneo cruzando el detector, no cortes reales |

Con `UMBRALES_POR_DEFECTO` sobrevive el **42%** (8 de 19). Causas: `unstable` 10,
`too_short` 5, `poor_exposure` 0.

**Regla que sale de aquí: ningún umbral entra sin haber visto la distribución real de la
métrica sobre la que se aplica.** Un test unitario con dos casos separados pasa igual aunque
el umbral vacíe el lote entero en producción.

### Y una propiedad que conviene no romper

Los umbrales de descarte van **por componente**, nunca sobre la nota general. Esa nota
promedia solo los componentes disponibles, así que **cambiará de valor cuando entre la
nitidez** (HU-023) sin que nadie toque nada. Dos tests de HU-103 fijan la propiedad: si
alguien mueve el criterio a la nota general, fallan.

---

## 4. Siguiente HU lista para DEV: **HU-104** o **HU-105**

| HU | Qué es | Dependencia | Estado |
|----|--------|-------------|--------|
| **HU-104** | Crop 9:16 de material horizontal (encuadre centrado configurable) | HU-101 ✅ | **lista** — la aritmética ya existe en `video.frame_to_vertical`, falta aplicarla a clips |
| **HU-105** | Secuenciado narrativo según plantilla del perfil | HU-103 ✅ · HU-135 ✅ | **lista** — `kept_scenes` y `assign_slots` ya existen; es cablearlos |

**HU-105 es la que más avanza el producto**: junta el descarte (HU-103) con el guion
(HU-135) y produce la línea de tiempo del reel. Ojo con un detalle: `assign_slots` reparte
por **ambiente**, y el etiquetado de ambientes (HU-032) no existe, así que hoy todo tramo que
exija ambiente queda como hueco. Con material sin etiquetar, el guion se llenará solo en los
tramos sin ambiente declarado.

---

## 5. Bloqueos y deuda declarada

| # | Qué | Impacto |
|---|---|---|
| **B-1** | **HU-023 (`ADR` de métrica de nitidez) no iniciada**, y el backlog **no la declara como dependencia de HU-102** aunque su enunciado la pida | La nitidez quedó fuera de HU-102 y de las causas de HU-103. Inconsistencia del backlog, anotada sin resolver |
| **B-2** | HU-100 (ingesta de clips con streaming) no iniciada | HU-102 muestrea cuadros por su cuenta. Cuando HU-100 llegue, revisar si el muestreo debe pasar por ella |
| **B-3** | HU-032 (etiquetado de ambientes) no iniciada | `assign_slots` deja como hueco todo tramo que exija ambiente. Bloquea el valor real de HU-105 |
| D-1 | `core/ports/` tiene un solo puerto y una sola implementación | Si al llegar HU-105 no aporta desacoplamiento real, el puerto cabe en `core/scene.py` |
| D-2 | `video/scene_scoring.py` al 98% | La línea sin cubrir es el caso en que ningún cuadro tiene contiguo — inalcanzable con clips válidos |
| D-3 | Umbral de detección de escenas en 27.0 | Sobre el video largo produce 5 escenas de menos de 1,5 s. Con 40 desaparecen. Calibración: HU-133 |
| D-4 | Los umbrales de descarte son un punto de partida medido, no calibrado | HU-133 los fija en el perfil. Si el negocio quiere conservar más del 42%, el parámetro a mover es la estabilidad |

---

## 6. Cómo retomar

```bash
git checkout develop && git pull
export PATH="$PATH:/c/ffmpeg/ffmpeg-9.0.1-essentials_build/bin"
uv sync
uv run pytest            # 780 passed, 1 skipped
uv run ruff check . && uv run ruff format --check . && uv run mypy src/
```

Validar con material real (7 videos del cliente, fuera del repo):

```bash
uv run python scripts/probar_escenas_insumos.py "D:/Proyectos/Bacano (Parcela)/Living/Fotos/cell"
```

**Los medios del cliente nunca entran al repo** (charter §6.6). `.gitignore` excluye
`items/**/insumos/*.{mp4,mov,mkv,avi}`; verificado que ningún video existe en el historial.
