# Cierre arquitectónico de la CLI — decisión definitiva

> **Documento de cierre.** No abre alternativas: fija la superficie, mapea las 112 HUs,
> documenta las inconsistencias y deja la migración lista para ejecutar.
> Fecha: 2026-08-06 · Arquitecto: Claude (orquestador-ejecutor ASDD)
>
> **Nada implementado.** `src/`, `tests/` y el backlog intactos.

---

## 0. Corrección respecto a la propuesta anterior

La propuesta previa fijaba **cinco** comandos: `scan`, `run`, `report`, `profile`, `label`.
Bajo las restricciones de esta ronda —*"no inventes nuevos requerimientos"*, *"no cambies el
alcance funcional de ninguna HU"*, *"no crear HUs nuevas salvo estrictamente
imprescindible"*— dos de ellos no sobreviven al filtro:

| Comando | Por qué no entra en la superficie oficial |
|---------|-------------------------------------------|
| `scan` | **Ninguna HU del backlog pide inspeccionar sin producir estado.** Es valioso —hay evidencia: HU-004 encontró 72/82 fotos mal marcadas y HU-013 encontró 15 grupos duplicados— pero es un requerimiento nuevo, y el pipeline funciona sin él. **No es imprescindible** |
| `profile` | HU-136 pide *mensajes de error accionables*, no un comando. Sus mensajes aparecen cuando cualquier comando carga el perfil. Un comando dedicado sería un requerimiento nuevo |

Ambos quedan como **capacidades reservadas** (§6): la arquitectura las admite de forma
aditiva, y su incorporación es una decisión de producto, no de diseño.

**La propiedad estructural no cambia por eso:** la superficie sigue sin crecer con el
pipeline. Es lo único que la decisión tenía que garantizar.

---

## 1. Superficie oficial de la CLI

### La decisión

**Tres comandos. Las etapas y los reportes son datos de un registro, no comandos.**

```
media-optimizer [opciones globales] <comando> [argumento] [opciones]

  run     <etapa>     ejecuta trabajo del pipeline
  report  <tipo>      presenta lo que el pipeline ya produjo
  label               corrección humana asistida
```

- `<etapa>` y `<tipo>` son **argumentos posicionales con `choices` tomadas de un registro**
  que vive en `pipeline/`. No son subcomandos anidados.
- Opciones globales: `--workspace`, `--profile`, `--log-level`, `--log-file`, `--quiet`,
  `--version`.

### Registro inicial

| `run <etapa>` | `report <tipo>` |
|---------------|-----------------|
| `ingest` · `analyze` · `develop` · `select` · `reel` · `all` | `inventory` · `analysis` · `develop` · `selection` · `reel` · `run` · `history` |

Añadir una etapa o un reporte es **añadir una entrada al registro**. `cli/` no se toca.

### Justificación

**Charter.** El §3 fija el principio de extensión del proyecto: *"todo criterio específico
del cliente entra como **datos** del perfil de negocio, nunca como código"*. Esta decisión
aplica la misma regla a las etapas: una etapa no es una capacidad distinta del sistema, es
material de trabajo del orquestador (HU-180). No introduce un principio nuevo — extiende el
que el proyecto eligió al nacer.

El §6.1 (determinismo) queda satisfecho porque el registro es una **tupla ordenada
explícita**, nunca descubrimiento por filesystem.

Y el §2 se preserva entero: `run select` existe, así que la galería ordenada —el entregable
de negocio— sigue siendo alcanzable.

**ADR-005.** Su umbral de reapertura es *">15 comandos, >150 líneas de parser, o un comando
con subcomandos anidados"*. Con la superficie del backlog (un comando por etapa), el
proyecto **cruza ese umbral por su propio crecimiento**: 6 comandos hoy, ≥12 al incorporar
los reportes que ya están escritos, >15 con video y verticales nuevas. Con esta decisión el
parser tiene **3 subparsers planos, para siempre**.

Es decir: **esta superficie es lo que mantiene válida la decisión de `argparse`.** La
alternativa la caduca sola.

La objeción seria —que cada etapa necesitaría flags propios, forzando subparsers anidados—
no aplica, y no por opinión: **HU-056 dice que el orden y los parámetros de los transforms
son datos del perfil**. Un `--clahe-clip` en la línea de comandos sería criterio estético
fuera del perfil, exactamente el `if` por cliente que el charter §3 prohíbe. Toda etapa
recibe lo mismo: workspace, perfil y opcionalmente un origen.

**Mantenibilidad.** El acoplamiento de `cli/` al pipeline es **constante**: tres módulos de
comando, independientemente de cuántas etapas existan. Bajo un comando por etapa, cada etapa
nueva añade un módulo y una entrada de parser, para siempre.

**Escalabilidad.** §5 de la propuesta anterior lo proyecta: a ~20 unidades de trabajo, un
comando por etapa da 20 módulos y un parser que cruza el umbral; esta decisión da 3 módulos
y un parser que no crece. A ~50, la primera es inviable y la segunda no cambia.

**Experiencia de uso.** Coste real y completo: el usuario escribe `run ingest` en vez de
`ingest` —un token más— y descubre las etapas con `run --help` en lugar de `--help`.
A cambio, `--help` explica **qué hace la herramienta** (ejecutar, leer, corregir) en vez de
enumerar las etapas internas del pipeline, que es información de implementación.

---

## 2. Matriz completa — las 112 HUs

**Ninguna HU queda sin mecanismo de ejecución.** Las HUs de librería lo tienen a través del
comando que las consume; la columna lo hace explícito.

**Leyenda:** `directa` = la HU es la superficie · `contenido` = la HU aporta el contenido que
un subcomando expone · `motor` = la HU es consumida por un comando sin superficie propia.

### E7 · Plataforma — 21 HUs

| HU | Comando | Subcomando | Responsabilidad | Etapa | Rol |
|----|---------|-----------|-----------------|-------|-----|
| 150 | — | — | Esqueleto del repo | — | infra |
| 151 | — | — | ADR gestor de entorno | — | infra |
| 152 | — | — | ADR stack de visión | — | infra |
| 153 | — | — | ADR catálogo local | — | infra |
| 154 | — | — | ADR stack de video | — | infra |
| 155 | *(global)* | — | Config externalizada: defaults bajo los argumentos | — | motor |
| 156 | *(global)* | `--log-level`, `--log-file` | Rastro estructurado | — | motor |
| 157 | — | — | Contrato `MediaAsset` | — | motor |
| 158 | — | — | Contrato `QualityReport` | — | motor |
| 159 | — | — | Contrato `Transform` | — | motor |
| 160 | — | — | Contrato `BusinessProfile` | — | motor |
| 161 | *(global)* | — | Excepciones → códigos de salida | — | motor |
| **162** | **todos** | — | **Parser raíz, despacho, códigos de salida** | — | **directa** |
| 163 | — | — | Gates de calidad locales | — | infra |
| 164 | — | — | Golden tests (invoca `main(argv)`) | — | infra |
| 165 | — | — | Benchmarks (`benchmarks/`, no CLI) | — | infra |
| 166 | — | — | Fixtures sintéticos de imagen | — | infra |
| 167 | — | — | Fixtures sintéticos de video | — | infra |
| 168 | `report` | `run` | `StageReport` por etapa | todas | contenido |
| 169 | — | — | Utilidades de determinismo | — | motor |
| **170** | **`report`** | **`history`** | Histórico de auditoría entre lotes | — | **directa** |

### E1 · Ingesta y catálogo — 19 HUs

| HU | Comando | Subcomando | Responsabilidad | Etapa | Rol |
|----|---------|-----------|-----------------|-------|-----|
| 001 | `run` | `ingest` | Escaneo determinista de carpeta | ingest | motor |
| 002 | `run` | `ingest` | Validación de formatos de imagen | ingest | motor |
| 003 | `run` | `ingest` | Validación de formatos de video | ingest | motor |
| 004 | `run` | `ingest` | Lectura segura de EXIF | ingest | motor |
| 005 | `run` | `ingest` | Orientación V/H | ingest | motor |
| 006 | `run` | `ingest` | Hash y duplicados exactos | ingest | motor |
| 007 | `report` | `inventory` | Flag compresión WhatsApp | ingest | contenido |
| 008 | `report` | `inventory` | Flag "bajo el nativo" | ingest | contenido |
| 009 | `report` | `inventory` | Cuarentena con causa | ingest | contenido |
| 010 | — | — | Capa de acceso al filesystem | todas | motor |
| 011 | `run` | `ingest` | Límites de memoria y dimensiones | ingest | motor |
| 012 | `run` | `ingest` | Persistencia del catálogo | ingest | motor |
| 013 | `run` | `ingest` | Re-ingesta idempotente | ingest | motor |
| 014 | `run` | `ingest` | Metadatos de video | ingest | motor |
| 015 | `report` | `inventory` | Agrupación por sesión de captura | ingest | contenido |
| 016 | *(global)* | `--workspace` | Directorio de trabajo no destructivo | todas | motor |
| **017** | **`run`** | **`ingest`** | **Carpeta → catálogo + resumen** | **ingest** | **directa** |
| **018** | **`report`** | **`inventory`** | **Tabla por asset del lote** | ingest | **directa** |
| 019 | `label` | — | Sidecar de etiquetas manuales | — | contenido |

### E2 · Análisis de calidad — 19 HUs

| HU | Comando | Subcomando | Responsabilidad | Etapa | Rol |
|----|---------|-----------|-----------------|-------|-----|
| 020 | `run` | `analyze` | Brillo medio | analyze | motor |
| 021 | `run` | `analyze` | % de negro aplastado | analyze | motor |
| 022 | `run` | `analyze` | % de altas luces quemadas | analyze | motor |
| 023 | `run` | `analyze` | ADR + métrica de nitidez | analyze | motor |
| 024 | `run` | `analyze` | Estimación de ruido | analyze | motor |
| 025 | `run` | `analyze` | Desenfoque de movimiento | analyze | motor |
| 026 | `run` | `analyze` | Temperatura de color | analyze | motor |
| 027 | `run` | `analyze` | Contraste global y por zonas | analyze | motor |
| 028 | `run` | `analyze` | Verticales inclinadas | analyze | motor |
| 029 | `run` | `analyze` | Score de exposición compuesto | analyze | motor |
| 030 | `run` | `analyze` | Veredicto técnico por asset | analyze | motor |
| 031 | — | — | ADR detección de ambientes | analyze | infra |
| **032** | **`label`** | — | **Etiquetado asistido de ambientes** | — | **directa** |
| 033 | `report` | `analysis` | Cobertura de ambientes del lote | analyze | contenido |
| 034 | `report` | `inventory` | Flag PII (rostros/placas) | analyze | contenido |
| 035 | `run` | `analyze` | `QualityReport` serializado | analyze | motor |
| **036** | **`report`** | **`analysis`** | **Tablas por score, estrellas, descartes** | analyze | **directa** |
| **037** | **`run`** | **`analyze`** | **Catálogo → reportes + flags** | **analyze** | **directa** |
| 038 | — | — | Golden test integral de análisis | analyze | infra |

### E3 · Revelado — 16 HUs

| HU | Comando | Subcomando | Responsabilidad | Etapa | Rol |
|----|---------|-----------|-----------------|-------|-----|
| 050 | `run` | `develop` | Corrección de perspectiva | develop | motor |
| 051 | `run` | `develop` | CLAHE por perfil | develop | motor |
| 052 | `run` | `develop` | White balance | develop | motor |
| 053 | `run` | `develop` | Recuperación de sombras | develop | motor |
| 054 | `run` | `develop` | Exposición hacia objetivo | develop | motor |
| 055 | `run` | `develop` | Control de saturación | develop | motor |
| 056 | `run` | `develop` | Pipeline componible (orden = perfil) | develop | motor |
| 057 | `report` | `develop` | Historial de transformaciones | develop | contenido |
| 058 | `run` | `develop` | Crop 4:5 para feed | develop | motor |
| 059 | `run` | `develop` | Salida 9:16 para stories | develop | motor |
| 060 | `run` | `develop` | Redimensionado al nativo | develop | motor |
| 061 | `run` | `develop` | Export JPEG sin PII | develop | motor |
| 062 | — | — | Golden tests del revelado | develop | infra |
| 063 | — | — | Presupuesto de rendimiento por foto | develop | infra |
| **064** | **`run`** | **`develop`** | **Lote → derivados en el workspace** | **develop** | **directa** |
| **065** | **`report`** | **`develop`** | **Antes/después del lote** | develop | **directa** |

### E4 · Ranking y selección — 10 HUs

| HU | Comando | Subcomando | Responsabilidad | Etapa | Rol |
|----|---------|-----------|-----------------|-------|-----|
| 070 | `run` | `select` | Score global por asset | select | motor |
| 071 | `run` | `select` | Candidatas a portada | select | motor |
| 072 | `run` | `select` | Orden narrativo de galería | select | motor |
| 073 | `run` | `select` | Cobertura en la selección | select | motor |
| 074 | `run` | `select` | Selección por formato de salida | select | motor |
| 075 | `run` | `select` | Near-duplicates para diversidad | select | motor |
| 076 | `report` | `selection` | Ranking explicable | select | contenido |
| 077 | `report` | `selection` | Matching contra plan de piezas | select | contenido |
| **078** | **`run`** | **`select`** | **Catálogo → selección + galería** | **select** | **directa** |
| 079 | — | — | Golden test de ranking | select | infra |

### E5 · Video y reels — 13 HUs

| HU | Comando | Subcomando | Responsabilidad | Etapa | Rol |
|----|---------|-----------|-----------------|-------|-----|
| 100 | `run` | `ingest` | Ingesta de clips (streaming) | ingest | motor |
| 101 | `run` | `reel` | Detección de escenas | reel | motor |
| 102 | `run` | `reel` | Score técnico por escena | reel | motor |
| 103 | `report` | `reel` | Descarte de escenas con causas | reel | contenido |
| 104 | `run` | `reel` | Crop 9:16 de material horizontal | reel | motor |
| 105 | `run` | `reel` | Secuenciado narrativo | reel | motor |
| 106 | `run` | `reel` | Recorte a duración objetivo | reel | motor |
| 107 | `run` | `reel` | Ensamblado con ffmpeg | reel | motor |
| 108 | `run` | `reel` | Normalización entre clips | reel | motor |
| 109 | `run` | `reel` | Export 1080×1920 | reel | motor |
| **110** | **`run`** | **`reel`** | **Clips → reel 9:16** | **reel** | **directa** |
| 111 | — | — | Golden test de reel | reel | infra |
| 112 | — | — | Presupuesto por minuto de material | reel | infra |

### E6 · Perfiles de negocio — 8 HUs

| HU | Comando | Subcomando | Responsabilidad | Etapa | Rol |
|----|---------|-----------|-----------------|-------|-----|
| 130 | *(global)* | `--profile` | Esquema del perfil y validación | todas | motor |
| 131 | *(global)* | `--profile` | Carga con defaults + overrides | todas | motor |
| 132 | — | — | Perfil `hospedaje` v1 (datos) | — | datos |
| 133 | — | — | Umbrales técnicos (datos) | — | datos |
| 134 | — | — | Pesos del score (datos) | — | datos |
| 135 | — | — | Plantillas narrativas (datos) | — | datos |
| 136 | *(global)* | `--profile` | Perfil hostil: mensajes accionables | todas | motor |
| 137 | — | — | Guía + perfil de vertical nueva | — | datos |

> **Nota sobre E6:** las 8 HUs quedan cubiertas por la opción global `--profile`, que carga y
> valida antes de ejecutar. HU-136 se prueba a través del camino de error de cualquier
> comando. **No hace falta un comando `profile` para que ninguna de estas HUs sea
> implementable ni verificable** — ver §6.

### E8 · Pipeline y reportes — 6 HUs

| HU | Comando | Subcomando | Responsabilidad | Etapa | Rol |
|----|---------|-----------|-----------------|-------|-----|
| 180 | `run` | *(todas)* | Orquestador: degrada y continúa | todas | motor |
| **181** | **`report`** | **`run`** | **Consolidado del run en Markdown** | — | **directa** |
| 182 | `run` | *(todas)* | Reanudación idempotente | todas | motor |
| 183 | `report` | `run --format jsonl` | Métricas de run en JSONL | todas | contenido |
| **184** | **`run`** | **`all`** | **Secuencia completa del pipeline** | all | **directa** |
| 185 | — | — | Smoke test E2E | — | infra |

### Resumen

| Rol | HUs |
|-----|-----|
| **directa** (es la superficie) | **12** — 017, 018, 032, 036, 037, 064, 065, 078, 110, 162, 170, 181, 184 → *13 con HU-162* |
| **contenido** (alimenta un subcomando) | 15 |
| **motor** (consumida por un comando) | 60 |
| **infra / datos** (sin superficie de usuario) | 24 |
| **Total** | **112 · ninguna sin mecanismo** |

---

## 3. Inconsistencias detectadas — documentadas, **no corregidas**

### 3.1 Conteos y numeración

| # | Inconsistencia | Evidencia |
|---|----------------|-----------|
| **C-1** | La cabecera declara **111 HUs**; hay **112** listadas | Recuento de filas `^| HU-` |
| **C-2** | Declara **P0: 43**; hay **48** | Recuento |
| **C-3** | Declara **P1: 41**; hay **43** | Recuento |
| **C-4** | Declara **P2: 22**; hay **19** | Recuento |
| **C-5** | Declara **P3: 5**; hay **2** | Recuento |
| **C-6** | La épica E7 declara el rango **HU-150–169**, pero existe **HU-170** | Encabezado de E7 vs la fila |

**Las cinco cifras del pie del backlog están mal.** C-6 sugiere el origen: HU-170 se añadió
después del cierre del rango y no se recalculó nada.

### 3.2 HUs sin mecanismo de ejecución en el backlog actual

| # | HU | Problema |
|---|----|----------|
| **C-7** | HU-018, 036, 065, 181 | Escritas como *"reporte"* **sin decir cómo las invoca el usuario**. Un reporte que nadie puede pedir no es un entregable |
| **C-8** | HU-032 | Dice *"vía CLI"* sin decir **cuál** comando |
| **C-9** | HU-170 | Dice *"herramienta versionada"* sin superficie |

**Esta es la causa raíz del bloqueo**, y es anterior a cualquier discusión de nombres.

### 3.3 Solapamientos de alcance

| # | HUs | Solapamiento |
|---|-----|--------------|
| **C-10** | HU-100 vs HU-003 + HU-014 | HU-100 (*"Ingesta de clips: validación, metadatos, streaming"*) **reenuncia** la validación de formatos de video (HU-003) y los metadatos de video (HU-014). Tres HUs para una responsabilidad |
| **C-11** | HU-181 vs HU-018 + HU-036 + HU-076 | HU-181 (*"consolidado: inventario + análisis + selección"*) **contiene** el inventario (018), el comparativo (036) y las trazas (076). No está claro si agrega o duplica |
| **C-12** | HU-170 vs HU-183 | Ambas acumulan métricas históricas: 170 de negocio (duplicados, formatos, cuarentena), 183 de rendimiento (tiempos, memoria). Adyacentes, con frontera no declarada |

### 3.4 Contradicciones entre documentos

| # | Contradicción | Detalle |
|---|---------------|---------|
| **C-13** | **Hitos vs backlog** | La tabla de hitos declara *"M3 — Selección y galería · `rank` / `select`"*. **`rank` no existe como comando en ninguna HU.** Dos nombres para una sola capacidad |
| **C-14** | Convención `ADR` del backlog | El backlog marca con `ADR` las HUs que cierran una decisión de stack (151, 152, 153, 154, 023, 031). Pero **ADR-004 nació de HU-010 y ADR-005 de HU-162**, ninguna marcada. La convención describe 3 de 5 ADRs existentes |
| **C-15** | Épica de HU-170 | Está en E7 (*Plataforma*) pero depende de HU-017 y su contenido es auditoría de lotes, más cercano a E8 (*Pipeline y reportes*) |

**Sin contradicciones entre el charter y el backlog**, ni entre ADR-005 y el backlog una vez
aplicada la migración de §4.

---

## 4. Migración mínima

**Prioridades respetadas:** 0 divisiones · 0 fusiones · **0 HUs nuevas** · historial intacto.

Ninguna HU cambia de alcance funcional. Todos los cambios son de **enunciado** —decir cómo
se invoca lo que la HU ya define— y de **metadatos del backlog**.

### 4.1 Enunciados que declaran su invocación (12)

| HU | Cambio de enunciado | Motivo | Impacto | Riesgo |
|----|---------------------|--------|---------|--------|
| 017 | `CLI ingest:` → `Etapa ingest (run ingest):` | Unifica con la superficie | Ninguno: mismo alcance | **Nulo** |
| 037 | `CLI analyze:` → `Etapa analyze (run analyze):` | Idem | Ninguno | Nulo |
| 064 | `CLI develop:` → `Etapa develop (run develop):` | Idem | Ninguno | Nulo |
| 078 | `CLI select:` → `Etapa select (run select):` | Idem | Ninguno | Nulo |
| 110 | `CLI reel:` → `Etapa reel (run reel):` | Idem | Ninguno | Nulo |
| 184 | `CLI run: pipeline completo` → `Secuencia all (run all): pipeline completo` | Idem | Ninguno | Nulo |
| 018 | `Reporte de inventario del lote` → `+ (report inventory)` | **Resuelve C-7** | Le da mecanismo | Nulo |
| 036 | `Reporte comparativo del lote` → `+ (report analysis)` | **Resuelve C-7** | Idem | Nulo |
| 065 | `Reporte antes/después` → `+ (report develop)` | **Resuelve C-7** | Idem | Nulo |
| 181 | `Reporte consolidado del run` → `+ (report run)` | **Resuelve C-7** | Idem | Nulo |
| 032 | `vía CLI` → `vía el comando label` | **Resuelve C-8** | Precisa lo que ya decía | Nulo |
| 170 | `herramienta versionada` → `+ (report history)` | **Resuelve C-9** | Le da mecanismo | Nulo |

**Archivos afectados:** `docs/blueprint/backlog.md` (12 líneas).

### 4.2 Corrección de conteos y rango (6)

| Cambio | Motivo | Riesgo |
|--------|--------|--------|
| `Total: 111` → `112` | C-1 | Nulo |
| `P0: 43` → `48` | C-2 | Nulo |
| `P1: 41` → `43` | C-3 | Nulo |
| `P2: 22` → `19` | C-4 | Nulo |
| `P3: 5` → `2` | C-5 | Nulo |
| `E7 · Plataforma (HU-150–169)` → `(HU-150–170)` | C-6 | Nulo |

**Archivo afectado:** `docs/blueprint/backlog.md` (2 líneas: encabezado E7 y pie).

### 4.3 Corrección de la tabla de hitos (1)

| Cambio | Motivo | Riesgo |
|--------|--------|--------|
| M3: `` `rank` / `select` `` → `` `run select` `` | C-13: `rank` no existe | Nulo |

Los hitos M1, M2 y M4 se reescriben a la superficie nueva (`run ingest`/`run analyze`,
`run develop`, `run reel`) por coherencia, sin cambiar qué entrega cada hito.

### 4.4 Arquitectura (1 archivo)

| Cambio | Motivo | Riesgo |
|--------|--------|--------|
| `arquitectura.md` §3: añadir que **el registro de etapas y reportes vive en `pipeline/`** y que `cli/` lo consulta en vez de conocerlo. Una flecha nueva en el diagrama | Es la propiedad que sostiene la decisión | **Bajo** — documento creado hoy, sin consumidores |

### 4.5 Documentación (2 archivos)

| Archivo | Cambio | Riesgo |
|---------|--------|--------|
| `.claude/CLAUDE.md` | Fila `cli/`: *"tres capacidades; las etapas son datos del registro"* | Nulo |
| `.claude/rules/cli.md` | Añadir: **un comando no puede llevar la lista de etapas escrita a mano**; se pide al registro | Nulo |

### 4.6 Spec de HU-162 (1 archivo)

| Cambio | Motivo | Riesgo |
|--------|--------|--------|
| Cerrar P-1 con esta decisión; confianza 78% → 93%; estado BLOQUEADA → LISTA PARA DEV | Es la pregunta que bloqueaba | Nulo |

### 4.7 Lo que **no** se toca

- **Ninguna HU cerrada** (23 en DONE): sus specs, closures y evidencia quedan intactos.
- **Ningún alcance funcional.**
- **`src/`, `tests/`, `pyproject.toml`, `uv.lock`.**
- **El charter**: esta decisión es una consecuencia de su §3, no una excepción.
- **C-10, C-11, C-12, C-14, C-15**: documentados, **sin acción**. Corregirlos exigiría
  redefinir alcances (C-10, C-11), reclasificar épicas (C-15) o reescribir una convención
  (C-14) — todo fuera de "migración mínima". Se dejan como deuda declarada.

**Total: 4 archivos, 12 enunciados, 9 líneas de metadatos, 0 HUs creadas, 0 divididas, 0 fusionadas.**

---

## 5. Plan de migración — orden exacto

> Ejecutable sin ambigüedad. Cada paso es independiente y verificable.

**Paso 1 — `docs/blueprint/backlog.md`: enunciados de etapa (6 líneas).**
Reescribir HU-017, 037, 064, 078, 110, 184 según §4.1. Sin tocar dependencias, prioridad ni
estimación.

**Paso 2 — `docs/blueprint/backlog.md`: enunciados de reporte y corrección (6 líneas).**
Reescribir HU-018, 036, 065, 181, 032, 170 según §4.1.

**Paso 3 — `docs/blueprint/backlog.md`: encabezado de E7 (1 línea).**
`(HU-150–169)` → `(HU-150–170)`.

**Paso 4 — `docs/blueprint/backlog.md`: pie de totales (1 línea).**
`Total: 112 HUs · P0: 48 · P1: 43 · P2: 19 · P3: 2`.

**Paso 5 — `docs/blueprint/backlog.md`: tabla de hitos (4 líneas).**
M1 → `run ingest` + `run analyze` + `report inventory` · M2 → `run develop` ·
M3 → `run select` · M4 → `run reel`.

**Paso 6 — `docs/blueprint/arquitectura.md`: registro en `pipeline/`.**
Añadir el apartado en §3 y la flecha `cli/ → registro de pipeline/` en el diagrama.
Añadir la regla A-6: *"`cli/` no contiene listas de etapas escritas a mano"*.

**Paso 7 — `.claude/CLAUDE.md`: fila `cli/` de la tabla de módulos.**

**Paso 8 — `.claude/rules/cli.md`: prohibición de listas de etapas escritas a mano.**

**Paso 9 — `items/HU-162/spec/spec_tecnica.md`.**
Cerrar P-1 con la decisión; actualizar §9 (confianza 93%, 0 bloqueantes) y el estado a
LISTA PARA DEV; ajustar los criterios de aceptación a los tres comandos.

**Paso 10 — `items/_metrics/gate-log.jsonl`.**
Registrar el evento de decisión arquitectónica y el gate de HU-162 superado en el
segundo intento.

**Paso 11 — Verificación.**
`pytest` + `ruff` + `mypy` deben seguir verdes (**no deberían cambiar: no se toca código**),
y ninguna búsqueda de `CLI \`` en el backlog debe devolver un comando fuera de la superficie.

**Paso 12 — Commit único** con el detalle de los 12 enunciados y las 6 correcciones.

---

## 6. Gate arquitectónico

### Arquitectura

**APROBADA**

### Confianza

**93 %**

El 7 % restante se reparte así, y ninguna parte impide implementar:

- **4 %** — C-11: la frontera entre HU-181 (consolidado) y las HUs de reporte que contiene
  (018, 036, 076) no está declarada. Afecta al *contenido* de `report run`, no a la
  superficie. Se resuelve cuando HU-181 entre a SPEC, con la información que hoy no existe.
- **2 %** — C-10: HU-100 solapa con HU-003 y HU-014. Afecta a la etapa `ingest` de video,
  toda en P2 y sin ninguna HU implementada aún.
- **1 %** — El registro de etapas vive en `pipeline/` (HU-180, no implementada). HU-162 debe
  construir el despacho contra un registro que al principio estará vacío. Es un contrato
  simple —una tupla de nombres— pero no está escrito todavía.

### Bloqueantes restantes

**Ninguno.**

La única pregunta bloqueante que existía —P-1 de HU-162, la superficie de comandos— queda
cerrada por §1. Ejecutados los 12 pasos de §5, HU-162 pasa el gate y la implementación
arranca sin más decisiones de diseño.

### Decisiones pendientes del arquitecto

Dos, **ambas aditivas y ninguna bloqueante**. La arquitectura las admite sin
reestructurarse: cada una añade un módulo en `cli/commands/` y nada más.

**D-1 · ¿Se incorpora `scan` (inspección sin producir estado)?**
- **Requiere:** 1 HU nueva en E1.
- **A favor, con evidencia medida:** HU-004 encontró 72 de 82 fotos mal marcadas y HU-013
  encontró 15 grupos de archivos duplicados. Un comando que deja mirar antes de escribir
  convierte esos hallazgos en algo que el usuario ve **antes** de generar estado.
- **En contra:** ningún requerimiento del backlog lo pide; el pipeline funciona sin él. Bajo
  la restricción *"no crear HUs nuevas salvo estrictamente imprescindible"*, **no califica**.
- **Recomendación:** aplazar a M2. No retrasa M1.

**D-2 · ¿Se incorpora `profile` (`show` / `validate` / `list`)?**
- **Requiere:** 1 HU nueva en E6.
- **A favor:** haría a HU-136 (*perfil hostil, mensajes accionables*) verificable de forma
  aislada, en vez de solo a través del camino de error de otro comando. Y HU-131 (*carga con
  defaults + overrides*) es difícil de inspeccionar sin un `show` que muestre el perfil
  **efectivo**.
- **En contra:** las 8 HUs de E6 son implementables y verificables sin él, vía `--profile`.
- **Recomendación:** aplazar hasta que HU-130/131/136 entren a SPEC y se vea si la falta de
  inspección estorba de verdad. **Decidirlo ahora sería especular.**

---

## 7. Criterio de éxito

Este documento deja la migración lista para ejecutar sin volver a discutir diseño:

- ✅ Superficie oficial fijada y justificada contra charter, ADR-005, mantenibilidad,
  escalabilidad y experiencia de uso.
- ✅ Las 112 HUs mapeadas a comando, subcomando, responsabilidad y etapa. **Ninguna sin
  mecanismo de ejecución.**
- ✅ 15 inconsistencias documentadas (C-1 a C-15), separando las que la migración corrige (9)
  de las que quedan como deuda declarada (6).
- ✅ Migración mínima: 4 archivos, 0 HUs nuevas, 0 divisiones, 0 fusiones, historial intacto.
- ✅ Plan de 12 pasos sin ambigüedad.
- ✅ Gate: **APROBADA · 93 % · 0 bloqueantes · 2 decisiones aditivas aplazadas.**

**La siguiente conversación puede empezar con "Ejecuta la migración arquitectónica".**
