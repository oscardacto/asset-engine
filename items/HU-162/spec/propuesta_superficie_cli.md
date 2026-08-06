# Propuesta arquitectónica — Superficie definitiva de la CLI

> Preparada para aprobación. **Ninguna línea de código escrita.**
> Resuelve la inconsistencia I-1 documentada en [`impacto_adr_005.md`](impacto_adr_005.md).
> Fecha: 2026-08-06 · Arquitecto: Claude (orquestador-ejecutor ASDD)

---

## 1. Auditoría completa del backlog

Las **112 HUs**, una por una. Sin omisiones.

> **Hallazgo previo, no relacionado con la CLI:** la cabecera del backlog declara *"Total:
> 111 HUs · P0: 43 · P1: 41 · P2: 22 · P3: 5"*. El recuento real es **112 HUs · P0: 48 ·
> P1: 43 · P2: 19 · P3: 2**. **Las cinco cifras están mal.** Se corrige en el plan de
> migración (§7.5).

**Leyenda de la columna ¿CLI?** — `directa` = la HU *es* una interacción de línea de
comandos · `indirecta` = su resultado se ve o se configura por la CLI, pero la HU es
librería · `no` = sin superficie de usuario.

### E7 · Plataforma — 21 HUs

| HU | Responsabilidad | ¿CLI? | Comando propuesto | Observaciones |
|----|-----------------|-------|-------------------|---------------|
| 150 | Esqueleto del repo | no | — | |
| 151 | ADR gestor de entorno | no | — | Cerrado |
| 152 | ADR stack de visión | no | — | Cerrado |
| 153 | ADR catálogo local | no | — | Cerrado |
| 154 | ADR stack de video | no | — | |
| 155 | Configuración externalizada | indirecta | *(todos)* | Provee los defaults que la frontera tipada resuelve |
| 156 | Logging estructurado | indirecta | *(global)* | `--log-level`, `--log-file` |
| 157 | Contrato `MediaAsset` | no | — | Cerrado |
| 158 | Contrato `QualityReport` | no | — | Cerrado |
| 159 | Contrato `Transform` | no | — | Cerrado |
| 160 | Contrato `BusinessProfile` | no | — | Cerrado |
| 161 | Jerarquía de excepciones | indirecta | *(global)* | Mapea a códigos de salida |
| **162** | **CLI base** | **directa** | *(infraestructura)* | Esta HU: parser raíz, despacho, códigos |
| 163 | Gates de calidad | no | — | |
| 164 | Framework de golden tests | indirecta | — | Invoca `main(argv)` en proceso |
| 165 | Framework de benchmarks | no | — | `benchmarks/`, no es CLI de usuario |
| 166 | Fixtures sintéticos de imagen | no | — | Cerrado |
| 167 | Fixtures sintéticos de video | no | — | |
| 168 | Contrato `StageReport` | indirecta | `report run` | Es lo que el reporte muestra |
| 169 | Utilidades de determinismo | no | — | Cerrado |
| **170** | **Histórico de auditoría de lotes** | **directa** | **`report history`** | ⚠️ **Sin comando en el backlog.** Octava HU que necesita superficie |

### E1 · Ingesta y catálogo — 19 HUs

| HU | Responsabilidad | ¿CLI? | Comando propuesto | Observaciones |
|----|-----------------|-------|-------------------|---------------|
| 001 | Escaneo determinista de carpeta | indirecta | `scan`, `run ingest` | **Motor compartido por ambos** |
| 002 | Validación de formatos de imagen | indirecta | `scan`, `run ingest` | Idem |
| 003 | Validación de formatos de video | indirecta | `scan`, `run ingest` | Idem |
| 004 | Lectura segura de EXIF | no | — | Cerrado |
| 005 | Orientación V/H | no | — | Cerrado |
| 006 | Hash y duplicados exactos | indirecta | `scan` | `scan` los muestra sin escribir nada |
| 007 | Compresión WhatsApp | indirecta | `report inventory` | |
| 008 | Flag "bajo el nativo" | indirecta | `report inventory` | |
| 009 | Cuarentena de corruptos | indirecta | `report inventory` | Su causa aparece ahí |
| 010 | Capa de acceso al filesystem | no | — | Cerrado |
| 011 | Límites de memoria | no | — | Cerrado |
| 012 | Persistencia del catálogo | no | — | Cerrado |
| 013 | Re-ingesta idempotente | indirecta | `run ingest` | Es su comportamiento, no un comando |
| 014 | Metadatos de video | no | — | |
| 015 | Agrupación por sesión de captura | indirecta | `report inventory` | |
| 016 | Directorio de trabajo | indirecta | *(global)* | `--workspace` |
| **017** | **Ingesta: carpeta → catálogo** | **directa** | **`run ingest`** | Hoy: "CLI `ingest`" |
| **018** | **Reporte de inventario del lote** | **directa** | **`report inventory`** | Hoy es un *reporte*, no un comando |
| 019 | Sidecar de etiquetas manuales | indirecta | `label` | Es el archivo que `label` escribe |

### E2 · Análisis de calidad — 19 HUs

| HU | Responsabilidad | ¿CLI? | Comando propuesto | Observaciones |
|----|-----------------|-------|-------------------|---------------|
| 020 | Brillo medio | no | — | |
| 021 | % de negro aplastado | no | — | |
| 022 | % de altas luces quemadas | no | — | |
| 023 | ADR + métrica de nitidez | no | — | |
| 024 | Estimación de ruido | no | — | |
| 025 | Desenfoque de movimiento | no | — | |
| 026 | Temperatura de color | no | — | |
| 027 | Contraste global y por zonas | no | — | |
| 028 | Verticales inclinadas | no | — | |
| 029 | Score de exposición | no | — | |
| 030 | Veredicto técnico por asset | no | — | |
| 031 | ADR detección de ambientes | no | — | |
| **032** | **Etiquetado asistido de ambientes** | **directa** | **`label`** | ⚠️ **Sin comando en ninguna de las dos superficies.** Detectada en la revisión anterior |
| 033 | Cobertura de ambientes del lote | indirecta | `report analysis` | |
| 034 | Flag PII (rostros/placas) | indirecta | `report inventory` | |
| 035 | `QualityReport` serializado | no | — | |
| **036** | **Reporte comparativo del lote** | **directa** | **`report analysis`** | Hoy es un *reporte*, no un comando |
| **037** | **Análisis: catálogo → reportes** | **directa** | **`run analyze`** | Hoy: "CLI `analyze`" |
| 038 | Golden test integral de análisis | no | — | |

### E3 · Revelado — 16 HUs

| HU | Responsabilidad | ¿CLI? | Comando propuesto | Observaciones |
|----|-----------------|-------|-------------------|---------------|
| 050 | Corrección de perspectiva | no | — | Parámetros del perfil |
| 051 | CLAHE por perfil | no | — | Idem |
| 052 | White balance | no | — | Idem |
| 053 | Recuperación de sombras | no | — | Idem |
| 054 | Exposición hacia objetivo | no | — | Idem |
| 055 | Control de saturación | no | — | Idem |
| 056 | Pipeline de revelado componible | indirecta | `run develop` | **El orden y los parámetros son datos del perfil** |
| 057 | Historial de transformaciones | indirecta | `report develop` | |
| 058 | Crop 4:5 para feed | no | — | |
| 059 | Salida 9:16 para stories | no | — | |
| 060 | Redimensionado al nativo | no | — | |
| 061 | Export JPEG sin PII | no | — | |
| 062 | Golden tests del revelado | no | — | |
| 063 | Presupuesto de rendimiento | no | — | |
| **064** | **Revelado: lote → derivados** | **directa** | **`run develop`** | Hoy: "CLI `develop`" |
| **065** | **Reporte antes/después** | **directa** | **`report develop`** | Hoy es un *reporte*, no un comando |

### E4 · Ranking y selección — 10 HUs

| HU | Responsabilidad | ¿CLI? | Comando propuesto | Observaciones |
|----|-----------------|-------|-------------------|---------------|
| 070 | Score global por asset | no | — | Pesos del perfil |
| 071 | Candidatas a portada | no | — | |
| 072 | Orden narrativo de galería | no | — | Plantilla del perfil |
| 073 | Cobertura en la selección | no | — | |
| 074 | Selección por formato de salida | no | — | |
| 075 | Near-duplicates | no | — | |
| 076 | Ranking explicable | indirecta | `report selection` | Las trazas se leen ahí |
| 077 | Matching contra plan de piezas | indirecta | `report selection` | |
| **078** | **Selección: catálogo → galería** | **directa** | **`run select`** | Hoy: "CLI `select`". **Produce el entregable de negocio del charter §2** |
| 079 | Golden test de ranking | no | — | |

### E5 · Video y reels — 13 HUs

| HU | Responsabilidad | ¿CLI? | Comando propuesto | Observaciones |
|----|-----------------|-------|-------------------|---------------|
| 100 | Ingesta de clips | indirecta | `run ingest` | **La misma etapa, otro tipo de medio** |
| 101 | Detección de escenas | no | — | Umbrales del perfil |
| 102 | Score técnico por escena | no | — | |
| 103 | Descarte de escenas | indirecta | `report reel` | |
| 104 | Crop 9:16 | no | — | |
| 105 | Secuenciado narrativo | no | — | Plantilla del perfil |
| 106 | Recorte a duración objetivo | no | — | |
| 107 | Ensamblado del reel | no | — | |
| 108 | Normalización entre clips | no | — | |
| 109 | Export 1080×1920 | no | — | |
| **110** | **Reel: clips → 9:16** | **directa** | **`run reel`** | Hoy: "CLI `reel`" |
| 111 | Golden test de reel | no | — | |
| 112 | Presupuesto por minuto | no | — | |

### E6 · Perfiles de negocio — 8 HUs

| HU | Responsabilidad | ¿CLI? | Comando propuesto | Observaciones |
|----|-----------------|-------|-------------------|---------------|
| 130 | Esquema del perfil y validación | indirecta | `profile validate` | |
| 131 | Carga con defaults + overrides | indirecta | `profile show` | Mostrar el perfil **efectivo** tras aplicar defaults |
| 132 | Perfil `hospedaje` v1 | no | — | Son datos |
| 133 | Umbrales técnicos | no | — | Datos |
| 134 | Pesos del score | no | — | Datos |
| 135 | Plantillas narrativas | no | — | Datos |
| **136** | **Perfil hostil: mensajes accionables** | **directa** | **`profile validate`** | ⚠️ **Sin comando en ninguna superficie.** Hoy su mensaje solo aparecería cuando una etapa falla |
| 137 | Guía + perfil de vertical nueva | indirecta | `profile validate` | Es la herramienta que valida la generalización |

### E8 · Pipeline y reportes — 6 HUs

| HU | Responsabilidad | ¿CLI? | Comando propuesto | Observaciones |
|----|-----------------|-------|-------------------|---------------|
| 180 | Orquestador de etapas | indirecta | `run` | **Es el motor de `run`, no un comando** |
| **181** | **Reporte consolidado del run** | **directa** | **`report run`** | Hoy es un *reporte*, no un comando |
| 182 | Reanudación idempotente | indirecta | `run` | Comportamiento, no comando |
| 183 | Métricas de run en JSONL | indirecta | `report run --format jsonl` · `report history` | |
| **184** | **Pipeline completo** | **directa** | **`run all`** | Hoy: "CLI `run`" |
| 185 | Smoke test E2E | no | — | |

### Resumen de la auditoría

| Categoría | HUs | |
|-----------|-----|---|
| Interacción **directa** por CLI | **12** | 017, 018, 032, 036, 037, 064, 065, 078, 110, 136, 170, 181, 184 → *13 contando HU-162* |
| Interacción **indirecta** | 30 | Su salida se ve o su comportamiento se configura desde la CLI |
| Sin superficie de usuario | 69 | Librería y dominio |

**Hallazgo central de la auditoría:** el backlog reconoce como "CLI" solo a **6** HUs
(017, 037, 064, 078, 110, 184) — las que ejecutan una etapa. Pero hay **12** que necesitan
superficie. Las **6 restantes** (018, 032, 036, 065, 136, 170, 181) están escritas como
"reportes" o "herramientas" **sin decir cómo las invoca el usuario**.

**Ese es el defecto real, y no es de nombres: el backlog nunca decidió cómo se leen los
resultados ni cómo el humano corrige a la máquina.** Cualquier superficie que solo discuta
los verbos de etapa deja esas 6 HUs sin resolver.

---

## 2. Análisis de las dos alternativas planteadas

### Alternativa A — la CLI define la arquitectura; el backlog se adapta

Superficie: `scan`, `ingest`, `inventory`, `process`, `report`.

| | |
|---|---|
| **HUs afectadas** | **13**: 017, 018, 036, 037, 064, 065, 078, 110, 181, 184 reescritas · 032, 136, 170 sin destino · 1 HU nueva para `scan` |
| **Documentos afectados** | `backlog.md`, `arquitectura.md`, `CLAUDE.md`, specs de HU-162 |
| **ADR afectados** | Ninguno. ADR-005 es agnóstico a los nombres |
| **Impacto** | 4 épicas tocadas. **`select` y `reel` pierden superficie**: HU-078 produce la galería ordenada, el entregable de negocio del charter §2 |
| **Ventajas** | Separa *mirar* de *producir* (`scan`), y reconoce que leer resultados es una capacidad propia (`inventory`, `report`) |
| **Riesgos** | `process` fusiona análisis, revelado y selección: **tres etapas con presupuestos de rendimiento distintos** (HU-063, HU-112) compartiendo un solo `StageReport`. Destruye la granularidad que HU-168 acaba de establecer |
| **Deuda técnica** | **Alta.** `inventory` y `report` son el mismo verbo con distinto sustantivo; en cuanto lleguen `report develop` y `report selection`, o se añaden comandos sueltos o se admite que `inventory` era `report inventory` desde el principio |

### Alternativa B — el backlog define la arquitectura; la CLI se adapta

Superficie: `ingest`, `analyze`, `develop`, `select`, `reel`, `run`.

| | |
|---|---|
| **HUs afectadas** | **0 reescrituras** de enunciado… pero **6 HUs siguen sin superficie** (018, 032, 036, 065, 136, 170) |
| **Documentos afectados** | Ninguno inmediato |
| **ADR afectados** | Ninguno hoy. **ADR-005 se reabre al llegar a 15 comandos** |
| **Impacto** | Aparentemente nulo, y ahí está el problema: **el defecto que la auditoría encontró queda sin resolver** |
| **Ventajas** | Cero migración. Verbos cortos y familiares |
| **Riesgos** | **El número de comandos crece con el pipeline.** Hoy 6; con los reportes que faltan, ≥12; con video completo y perfiles nuevos, >15 → **cruza el umbral de reapertura de ADR-005 por su propio crecimiento** |
| **Deuda técnica** | **Alta y creciente.** Cada etapa nueva = un comando nuevo = un módulo nuevo en `commands/` + una entrada en el parser. El acoplamiento de la CLI al pipeline crece linealmente **para siempre** |

### Lo que ambas comparten

Las dos **fusionan la superficie con las etapas del pipeline**: A lo hace agrupando, B lo
hace uno a uno. En las dos, *"qué comandos hay"* es una consecuencia de *"qué etapas
existen"*. Por eso ninguna resuelve las 6 HUs de reporte y corrección: esas no son etapas.

---

## 3. Tercera alternativa — **las etapas son datos, no comandos**

### El razonamiento

El charter §3 fija el principio de extensión del proyecto:

> *"todo criterio específico del cliente entra como **datos** del perfil de negocio, nunca
> como código."*

La auditoría muestra que **la misma regla aplica a las etapas**. Una etapa del pipeline no
es una capacidad distinta del sistema: es *material de trabajo* del orquestador (HU-180).
Que exista `develop` no cambia lo que el usuario puede hacer —ejecutar trabajo— sino qué
trabajo hay disponible.

Si las etapas son datos, la CLI expone **capacidades**, y la lista de etapas sale del
registro del pipeline. Añadir `reel` deja de tocar la CLI.

### Las capacidades reales del sistema

Derivadas de la auditoría, no inventadas. Cada una responde a una pregunta distinta del
usuario y **ninguna se puede expresar en términos de otra**:

| Capacidad | Pregunta que responde | HUs que la necesitan |
|-----------|----------------------|----------------------|
| **`scan`** | *"¿Qué hay en esta carpeta, antes de que toques nada?"* | 001, 002, 003, 006 |
| **`run`** | *"Haz el trabajo."* | 017, 037, 064, 078, 110, 184, 180, 182 |
| **`report`** | *"¿Qué salió de eso?"* | 018, 036, 065, 170, 181, 183, 076 |
| **`profile`** | *"¿Con qué criterio va a trabajar, y es válido?"* | 130, 131, 136, 137 |
| **`label`** | *"La máquina se equivocó; corrígelo."* | 019, 032 |

**Cinco capacidades, y cubren las 12 HUs que necesitan superficie** — incluidas las 6 que
ninguna de las otras alternativas resolvía.

### Por qué esto no es "A con otros nombres"

En A, `process` **fusiona** tres etapas: el usuario pierde la capacidad de ejecutar solo el
revelado. En C, `run develop` sigue existiendo — lo que cambia es que `develop` es un
**valor**, no un comando. La granularidad se conserva entera; lo que desaparece es el
acoplamiento entre el tamaño del pipeline y el tamaño de la CLI.

### La objeción que hay que responder: ¿y los parámetros propios de cada etapa?

Es la crítica seria a C: si `develop` necesitara `--clahe-clip 2.0`, haría falta un
subparser por etapa, y eso **cruzaría el umbral de ADR-005** (*"un comando con subcomandos
anidados"*).

**No los necesita, y no es una opinión — lo prohíbe el charter.** HU-056 dice literalmente:
*"orden y parámetros de transforms **declarados en el perfil**"*. Un `--clahe-clip` en la
línea de comandos sería criterio estético fuera del perfil, es decir, exactamente el
`if` por cliente que el charter §3 prohíbe.

Consecuencia verificable: **toda etapa recibe lo mismo** —workspace, perfil, y opcionalmente
un origen—, así que la etapa es un argumento posicional con `choices` tomadas del registro.
Un valor, no un subparser. El parser se mantiene plano y diminuto **para siempre**.

### Comprobación contra los cinco criterios exigidos

| Criterio | A | B | **C** | Evidencia |
|----------|---|---|-------|-----------|
| Menor acoplamiento | medio | **alto** | **mínimo** | En C, `cli/` no cambia al añadir una etapa: el registro vive en `pipeline/` |
| Menor deuda técnica | alta | alta y creciente | **mínima** | 5 subparsers constantes vs 6→12→>15 |
| Menor impacto en el backlog | 13 HUs, 1 nueva | 0 pero deja 6 sin resolver | **12 HUs, solo el enunciado; alcance intacto** | §7 |
| Mayor escalabilidad | mala (fusiona) | mala (crece lineal) | **constante** | §5 |
| Coherencia con el charter | parcial | parcial | **total** | Aplica §3 —"datos, no código"— a las etapas |

**No existe una cuarta alternativa mejor.** Se descartaron dos por evidencia:

- **Un comando por HU** (12 comandos): cruza el umbral de ADR-005 antes de empezar y acopla
  la CLI al backlog, no al dominio.
- **Un solo comando con `--action`**: colapsa cinco capacidades ortogonales en un enumerado;
  el `--help` deja de poder explicar qué hace la herramienta, y las entradas de `scan`
  (una carpeta) y de `report` (un workspace) son incompatibles en una sola firma.

---

## 4. Diseño definitivo de la CLI

### 4.1 `scan` — inspeccionar sin producir nada

| | |
|---|---|
| **Responsabilidad** | Responder qué hay en una carpeta y qué pasaría con ello, **sin escribir nada en disco** |
| **Entradas** | `origen` (carpeta) · `--recursive/--no-recursive` |
| **Salidas** | Solo consola: conteos por formato, duplicados exactos, ilegibles, tamaño total |
| **Contratos** | `ScanArgs(source, recursive)` → lista de `MediaAsset` en memoria |
| **HUs** | 001, 002, 003, 006 *(motor)* · **HU nueva `HU-020x`** para el comando |
| **NO hace** | No crea workspace · no escribe catálogo · no aparta a cuarentena · **no requiere perfil** |

**Justificación medida:** en el lote real, HU-004 encontró **72 de 82 fotos mal marcadas** por
un defecto de EXIF y HU-013 encontró **15 grupos de archivos con el mismo contenido**. Un
comando que deja mirar antes de escribir convierte esos hallazgos en algo que el usuario ve
**antes** de generar estado, no después.

### 4.2 `run` — ejecutar trabajo del pipeline

| | |
|---|---|
| **Responsabilidad** | Ejecutar una etapa registrada, o la secuencia completa |
| **Entradas** | `etapa` (posicional; `choices` del registro de `pipeline/`) · `origen` (solo `ingest`) · `--force` · `--resume` |
| **Salidas** | Estado en el workspace + resumen en consola + `StageReport` por etapa |
| **Contratos** | `RunArgs(stage, source, force, resume)` → `pipeline.execute(stage, RunContext)` → `tuple[StageReport, ...]` |
| **HUs** | `ingest`→017 · `analyze`→037 · `develop`→064 · `select`→078 · `reel`→110 · `all`→184 · motor→180 · `--resume`→182 |
| **NO hace** | No decide criterios (vienen del perfil) · no formatea reportes (eso es `report`) · **no conoce la lista de etapas: se la pregunta a `pipeline/`** |

**`run all` no es una etapa más**: es la secuencia completa que HU-184 define. Se registra
como una entrada especial del registro, no como un `if` en la CLI.

### 4.3 `report` — leer lo que el pipeline produjo

| | |
|---|---|
| **Responsabilidad** | Presentar, en forma legible, algo que ya está en el workspace |
| **Entradas** | `tipo` (posicional: `inventory`, `analysis`, `develop`, `selection`, `reel`, `run`, `history`) · `--format {texto,markdown,jsonl}` |
| **Salidas** | Consola y/o archivo en `reports/` del workspace |
| **Contratos** | `ReportArgs(kind, output_format)` → lee el catálogo → texto determinista |
| **HUs** | `inventory`→018 · `analysis`→036 · `develop`→065 · `selection`→076 · `reel`→103 · `run`→181, 183, 168 · `history`→170 |
| **NO hace** | **No calcula nada.** Si un dato no está en el workspace, el reporte dice que falta esa etapa, no la ejecuta |

**Es la capacidad que ninguna de las dos alternativas anteriores reconocía**, y a la que
pertenecen **6 HUs** que hoy están escritas como "reportes" sin decir cómo se invocan.

### 4.4 `profile` — inspeccionar y validar el criterio de negocio

| | |
|---|---|
| **Responsabilidad** | Mostrar el perfil efectivo y validarlo **antes** de gastar una ejecución |
| **Entradas** | `accion` (`show`, `validate`, `list`) · `nombre` (opcional) |
| **Salidas** | Consola. `validate` sale con `3` si el perfil es inválido |
| **Contratos** | `ProfileArgs(action, name)` → `BusinessProfile` o error accionable |
| **HUs** | 130, 131 (`show` muestra el perfil **efectivo**, con defaults aplicados) · **136** · 137 |
| **NO hace** | No edita perfiles · no los genera |

**HU-136** —*"perfil hostil o incompleto: mensajes de error accionables, nunca stacktrace"*—
**no tenía dónde vivir**. Sin `profile validate`, su mensaje solo aparecería cuando una
etapa ya empezó a fallar, y la HU sería casi imposible de probar de forma aislada.

### 4.5 `label` — corrección humana asistida

| | |
|---|---|
| **Responsabilidad** | Que una persona confirme o corrija lo que la máquina propuso, y que eso **sobreviva a las re-ingestas** |
| **Entradas** | `--asset` o lote completo · `--accept-all` |
| **Salidas** | Sidecar de etiquetas (HU-019) |
| **Contratos** | `LabelArgs(asset, accept_all)` → sidecar |
| **HUs** | **032** · 019 |
| **NO hace** | No modifica el catálogo · no reprocesa · no toca los originales |

**No es una etapa del pipeline** y por eso no vive bajo `run`: es interactiva, la decide un
humano, y su salida es una entrada del pipeline, no un producto suyo. HU-032 llevaba dos
revisiones sin comando asignado.

### 4.6 Contexto global

`--workspace` · `--profile` · `--log-level` · `--log-file` · `--quiet` · `--version`.
`scan` y `profile list` son los únicos que funcionan **sin** workspace.

### 4.7 Estructura resultante

```
src/media_optimizer/cli/
├── main.py              parser raíz + despacho
├── exit_codes.py
├── errors.py
└── commands/
    ├── scan.py          ─┐
    ├── run.py            │  cinco módulos.
    ├── report.py         │  Este número NO cambia
    ├── profile.py        │  cuando crece el pipeline.
    └── label.py         ─┘
```

---

## 5. Proyección de crecimiento

| Escenario | Alternativa A | Alternativa B | **Alternativa C** |
|-----------|---------------|---------------|-------------------|
| **Hoy** (6 etapas, 7 reportes) | 5 comandos, `process` ya fusiona 3 etapas | 6 comandos + 6 HUs sin superficie | **5 comandos** |
| **~20 unidades de trabajo** | Comandos sueltos o más fusiones | **20 comandos → cruza el umbral de ADR-005** | **5 comandos.** 20 entradas de registro en `pipeline/` |
| **~50 unidades** | Inviable | **50 módulos en `commands/`; parser >400 líneas** | **5 comandos.** El parser no crece |
| **Perfiles de negocio nuevos** | 0 cambios | 0 cambios | **0 cambios** — son datos (charter §3) |
| **Pipeline nuevo** (p. ej. vertical de producto) | Comandos nuevos | Comandos nuevos por etapa | **0 comandos**; entradas de registro |
| **Motor nuevo** (cambiar PySceneDetect) | 0 cambios | 0 cambios | **0 cambios** |

**El resultado decisivo:** las alternativas A y B hacen que **ADR-005 se reabra por
crecimiento propio** — su umbral es *">15 comandos o >150 líneas de parser"*, y B lo cruza
solo con las HUs que ya están escritas. **C mantiene la decisión de ADR-005 válida
indefinidamente**, porque el parser deja de crecer con el producto.

Dicho de otro modo: **C es lo que hace que la decisión de `argparse` siga siendo correcta
dentro de dos años.** Las otras dos la caducan.

---

## 6. Compatibilidad — verificación cruzada

| Documento | ¿Compatible? | Verificación |
|-----------|--------------|--------------|
| **Charter §3** (perfiles como datos) | ✅ **Refuerza** | C aplica el mismo principio a las etapas |
| **Charter §2** (galería ordenada) | ✅ **Lo rescata** | `run select` existe; en A se perdía |
| **Charter §6.1** (determinismo) | ✅ | El registro es una tupla ordenada, no descubrimiento por filesystem |
| **ADR-005** | ✅ **Lo protege** | Sin subparsers anidados; parser plano y constante |
| **ADR-001–004** | ✅ | Sin relación |
| **arquitectura.md §3** | ✅ | `cli/` más delgada: el registro vive en `pipeline/` |
| **arquitectura.md A-4** | ✅ | `argparse` sigue confinado a `cli/` |
| **CLAUDE.md** (`cli/` capa delgada) | ✅ | Cinco módulos que traducen y despachan |
| **`.claude/rules/cli.md`** | ✅ | El patrón de 4 piezas aplica igual, 5 veces |
| **Reglas ASDD** | ✅ | Cada HU conserva su entregable propio y verificable |
| **Backlog** | ⚠️ **Requiere migración** | §7 — solo enunciados; **ningún alcance cambia** |

**Ninguna contradicción detectada.**

---

## 7. Plan de migración del backlog — **preparado, no ejecutado**

### 7.1 Se renombran (10) — cambia el enunciado, **no el alcance**

| HU | Antes | Después |
|----|-------|---------|
| 017 | CLI `ingest`: carpeta → catálogo | Etapa `ingest` del pipeline, invocable con `run ingest` |
| 037 | CLI `analyze` | Etapa `analyze`, invocable con `run analyze` |
| 064 | CLI `develop` | Etapa `develop`, invocable con `run develop` |
| 078 | CLI `select` | Etapa `select`, invocable con `run select` |
| 110 | CLI `reel` | Etapa `reel`, invocable con `run reel` |
| 184 | CLI `run`: pipeline completo | Secuencia `all` del registro, invocable con `run all` |
| 018 | Reporte de inventario del lote | Reporte `inventory`, invocable con `report inventory` |
| 036 | Reporte comparativo del lote | Reporte `analysis`, invocable con `report analysis` |
| 065 | Reporte antes/después | Reporte `develop`, invocable con `report develop` |
| 181 | Reporte consolidado del run | Reporte `run`, invocable con `report run` |

### 7.2 Se les asigna superficie (3) — hoy no tenían ninguna

| HU | Acción |
|----|--------|
| **032** | Etiquetado asistido → **`label`**. Ya decía "vía CLI" sin decir cuál |
| **136** | Perfil hostil → **`profile validate`**. Le da un lugar donde probarse aislada |
| **170** | Histórico de auditoría → **`report history`** |

### 7.3 Se crea (1)

| HU | Enunciado propuesto | Épica | Prio | Est |
|----|--------------------|-------|------|-----|
| **HU-020a** | Comando `scan`: inspección de una carpeta sin producir estado (conteos, duplicados, ilegibles) | E1 | P0 | S |

### 7.4 Se dividen o fusionan

**Ninguna.** Es la propiedad más valiosa de C: ningún alcance se parte ni se junta, así que
ninguna HU cerrada se invalida y ninguna estimación cambia.

### 7.5 Corrección de totales (independiente de la CLI)

`Total: 111 → **113**` (112 actuales + HU-020a) · `P0: 43 → 49` · `P1: 41 → 43` ·
`P2: 22 → 19` · `P3: 5 → 2`.

### 7.6 Permanecen intactas

**Las 98 restantes.** El 87% del backlog no se toca.

---

## 8. Recomendación técnica

**Se adopta la alternativa C: las etapas y los reportes son datos del registro; la CLI
expone cinco capacidades.**

La razón no es que sea más elegante, sino que es **la única de las tres que resuelve el
defecto que la auditoría encontró**: el backlog nunca decidió cómo se leen los resultados
(6 HUs) ni cómo el humano corrige a la máquina (2 HUs). A y B discuten los verbos de etapa,
y esas 8 HUs no son etapas.

Los tres argumentos que la sostienen, en orden de peso:

1. **Cobertura.** C cubre las 12 HUs con superficie. A deja 3 sin destino; B deja 6.
2. **Escala.** El tamaño de la CLI deja de depender del tamaño del pipeline. Es lo que
   mantiene válida la decisión de ADR-005 más allá de las 15 unidades de trabajo; A y B la
   caducan por crecimiento propio.
3. **Coherencia.** Es la aplicación del principio que el charter §3 ya fijó para los
   perfiles. No introduce una idea nueva: extiende la que el proyecto eligió al nacer.

**Coste honesto de la recomendación:** el usuario escribe `run ingest` en vez de `ingest`
—un token más— y la lista de etapas se descubre con `run --help` en lugar de con `--help`.
Es el precio completo, y es el único.

---

## 9. Criterios de aceptación — respondidos

**1 · ¿Qué comandos tendrá la CLI?** Cinco: `scan`, `run`, `report`, `profile`, `label`.

**2 · ¿Qué HU implementa cada uno?**

| Comando | HU del comando | HUs de su contenido |
|---------|----------------|---------------------|
| `scan` | **HU-020a** (nueva) | 001, 002, 003, 006 |
| `run` | HU-162 (despacho) + HU-180 (motor) | 017, 037, 064, 078, 110, 184, 182 |
| `report` | HU-162 (despacho) | 018, 036, 065, 076, 103, 170, 181, 183 |
| `profile` | HU-136 | 130, 131, 137 |
| `label` | HU-032 | 019 |

**3 · ¿Qué responsabilidad tiene cada uno?** §4, con entradas, salidas, contratos y —
explícitamente— qué **no** hace cada uno.

**4 · ¿Cómo crecerá el sistema dentro de un año?** §5. Con ~20 unidades de trabajo la CLI
**sigue teniendo cinco comandos** y el parser no crece; las etapas y reportes nuevos son
entradas de registro en `pipeline/`, y `cli/` no se toca.

**5 · ¿Qué cambios requiere el backlog?** §7: **10 renombres de enunciado, 3 asignaciones de
superficie, 1 HU nueva, 0 divisiones, 0 fusiones**, más la corrección de los cinco totales.
98 HUs (87%) intactas.

**6 · ¿Qué cambios requiere la arquitectura?** `arquitectura.md`: añadir que el **registro de
etapas y reportes vive en `pipeline/`**, y que `cli/` lo consulta en vez de conocerlo. Es un
apartado nuevo en §3 y una flecha en el diagrama. Las cinco reglas verificadas siguen igual.

**7 · ¿Qué cambios requiere la documentación?** `CLAUDE.md`: la fila `cli/` pasa a decir
"cinco capacidades; las etapas son datos del registro". `.claude/rules/cli.md`: añadir que un
comando **no** puede llevar una lista de etapas escrita a mano. El charter **no cambia** —
esta propuesta es una consecuencia de su §3, no una excepción.

---

## Estado

**Pendiente de aprobación.** Aprobada, HU-162 pasa de 78% a ~92% de confianza, la pregunta
bloqueante P-1 se cierra y la implementación arranca sin más decisiones de diseño pendientes.

Ejecutar §7 (migración del backlog) es requisito previo a escribir la primera línea, y es
trabajo de documentación: no toca código.
