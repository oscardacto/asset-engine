# Spec Técnica `HU-154` — `ADR del stack de video + ejecutor de FFmpeg`

> **Estado:** LISTA PARA DEV (parcial) — ver §9
> **Fecha de generación:** 2026-09-05 · **Regularizada:** 2026-09-05
> **Confianza global:** 88% para la capa de construcción · **0%** para la de ejecución real
> **ADR resultante:** [ADR-006](../../../docs/blueprint/adr/ADR-006-stack-video.md) — **Propuesto**

> ⚠️ **Nota de honestidad procesal.** Esta spec se escribe **después** de que el código se
> implementara y se integrara a `develop` (`c92074d`). Eso incumple la Regla de Oro nº 1 del
> proyecto: *«No iniciar `dev/` sin gate de spec aprobado»*. Se documenta como regularización
> y así queda marcado en el gate-log — **no se presenta como si el gate se hubiera emitido a
> tiempo**. La auditoría de gobernanza lo detectó y el registro conserva esa verdad.

---

## 1. Resumen ejecutivo

- **Qué se pide:** decidir cómo el proyecto invoca el procesamiento de video, y construir la
  capa que lo hace.
- **Para quién:** las 13 HUs de E5, más HU-003, HU-014 y HU-167.
- **Módulo:** `media_optimizer.video.ffmpeg_executor`.
- **No obvio:** el riesgo de esta HU no es elegir la librería — es que **ffmpeg recibe rutas
  y las abre por su cuenta**, exactamente el patrón que en HU-156 se midió destructivo en la
  biblioteca estándar, donde un archivo llamado `NUL.log` hacía que cada registro se
  descartara **sin error**. Por eso el backlog exige validar la matriz de rutas antes de
  adoptar la cadena, y por eso esa validación no puede darse por supuesta.

---

## 2. Alcance

### 2.1 IN
- ADR-006: alternativas evaluadas, decisión y política de determinismo.
- `FfmpegResult`: qué devolvió la herramienta.
- `build_command` / `build_probe_command`: construcción de peticiones con las banderas de
  reproducibilidad ya puestas.
- `run`: ejecución que **degrada en vez de lanzar**.
- `probe_filtergraph`: validación de un grafo sin renderizar.
- `detect_version` / `log_version`: registro de con qué versión se produjo cada salida.
- `normalized_segment`: reinicio de marcas de tiempo antes de cualquier filtro.

### 2.2 OUT
- **Instalar el binario** → decisión del equipo; es una dependencia externa.
- **PySceneDetect** → se adopta con HU-101, que es cuando hace falta.
- **Detección de escenas, crop, secuenciado, ensamblado** → sus propias HUs de E5.
- **Audio** → no existe en el charter ni en el backlog.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | El binario no está instalado | `FfmpegResult(ok=False)` con mensaje claro; nunca una traza |
| 2 | El proceso se cuelga | Se corta a los 900 s y se reporta |
| 3 | El grafo tiene un filtro inexistente | Se detecta en la validación silenciosa, en milisegundos |
| 4 | Ruta larga o con nombre de dispositivo | Pasa por la capa de ADR-004 — **pendiente de validar contra el binario real** |
| 5 | La salida de `-version` tiene otro formato | Devuelve `None` y lo advierte; no inventa una versión |

---

## 3. Componentes

| Componente | Cambio | Verificado |
|---|---|---|
| `docs/blueprint/adr/ADR-006-stack-video.md` | nuevo | ✅ |
| `src/media_optimizer/video/ffmpeg_executor.py` | nuevo | ✅ |
| `src/media_optimizer/ingest/filesystem.py` | añade `find_executable` | ✅ |
| `tests/video/test_ffmpeg_executor.py` | nuevo | ✅ |
| `tests/test_arquitectura.py` | vigila `subprocess` | ✅ |

### 3.1 Reutilizables
| Componente | ¿Reutilizar? | Justificación |
|---|---|---|
| `ingest.filesystem` (HU-010) | **Sí, obligatorio** | ffmpeg abre archivos por su cuenta; las rutas se traducen antes |
| `core.errors.CorruptMediaError` (HU-161) | Sí | Un clip que la herramienta rechaza se aparta como cualquier medio corrupto |
| `logs` (HU-156) | Sí | El rastro de cada invocación y de la versión detectada |

---

## 4. Modelo de datos

`FfmpegResult(ok, stderr, command, stdout)` — inmutable, con `failure_reason` que extrae la
línea del error que explica el fallo.

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|-------|--------|-------------|
| RN-1 | Determinismo | charter §6.1 | Cinco banderas obligatorias en el ejecutor |
| RN-2 | Un medio corrupto degrada, no tumba el lote | charter | `run` no lanza excepción |
| RN-3 | Todo acceso a disco por la capa | ADR-004 | Rutas traducidas antes de entregarlas |
| RN-4 | `core/` sin IO | CLAUDE.md | Prohibido importar `subprocess` y `video` |
| RN-5 | Sin `shell=True` | `python.md` | Lista de argumentos siempre |
| RN-6 | Cobertura ≥80% del módulo tocado | Pre-Flight | Evidencia al cierre |

---

## 6. Criterios de aceptación en BDD

### CA-1 · Las banderas de reproducibilidad no se pueden olvidar
```gherkin
DADO QUE un llamador construye una petición de procesamiento de video
CUANDO  arma el comando sin escribir ninguna bandera de reproducibilidad
ENTONCES el comando incluye el reparto en un solo hilo, la ausencia de espera de
         teclado y el descarte de metadatos heredados
```

### CA-2 · Las rutas se traducen antes de entregarlas al binario
```gherkin
DADO QUE la herramienta externa abre los archivos por su cuenta
CUANDO  se construye un comando con rutas de entrada y de salida
ENTONCES cada ruta aparece en el comando en la forma que el sistema exige para
         abrirla de verdad, y no en su forma original
```

### CA-3 · El reinicio de marcas de tiempo va primero y siempre
```gherkin
DADO QUE un segmento recortado conserva las marcas de tiempo de su origen
CUANDO  se encadenan filtros para ese segmento
ENTONCES el reinicio de marcas de tiempo es el primer filtro de la cadena,
         incluso si no se pidió ningún otro filtro
```

### CA-4 · Un fallo del binario degrada ese clip y no el lote
```gherkin
DADO QUE la herramienta externa rechaza una petición
CUANDO  el pipeline la ejecuta
ENTONCES no se lanza ninguna excepción, el resultado indica que falló, el rastro
         registra la causa, y quien llama decide si aparta el clip y continúa
```

### CA-5 · Un grafo inválido se detecta sin renderizar
```gherkin
DADO QUE renderizar un lote cuesta minutos
CUANDO  se valida un grafo de filtros antes de usarlo
ENTONCES la comprobación usa una fuente generada, descarta la salida, no escribe
         ningún archivo, y responde en milisegundos
```

### CA-6 · La versión del binario queda registrada
```gherkin
DADO QUE la herramienta externa evoluciona por su cuenta
CUANDO  el pipeline la detecta
ENTONCES la versión queda en el rastro estructurado, y si no se puede determinar
         se advierte en vez de inventar un valor
```

### CA-7 · Lanzar procesos externos está confinado a la capa de video
```gherkin
DADO QUE lanzar un proceso externo es tocar el disco por delegación
CUANDO  se revisa el código de producción
ENTONCES ningún módulo fuera de la capa de video importa el lanzador de procesos,
         y el dominio puro tampoco importa la capa de video
```

### CA-8 · La matriz de rutas se valida contra el binario real — **PENDIENTE**
```gherkin
DADO QUE el backlog prohíbe adoptar la cadena sin validarla
CUANDO  el binario esté instalado en la máquina de referencia
ENTONCES lee y escribe correctamente con rutas largas, con nombres que coinciden
         con dispositivos del sistema, y con la forma extendida de la plataforma
```

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|----------|-------------------|
| A-1 | `subprocess` basta; no hace falta una librería envoltorio | Reescribir dos funciones |
| A-2 | Las cinco banderas cubren el determinismo del ensamblado | Añadir banderas al ejecutor, aditivo |
| A-3 | **ffmpeg acepta la forma extendida de ruta** | **Alto: habría que rediseñar la entrega de rutas.** NO VERIFICADO |
| A-4 | 900 s bastan para un reel | Cambiar una constante |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R-1 | **ffmpeg rechaza o malinterpreta la forma extendida** | desconocida | **alto** | CA-8; hasta entonces el ADR no se acepta |
| R-2 | Alguien invoque el binario fuera de la capa | media | alto | Regla verificada en el test de arquitectura |
| R-3 | Un cambio de versión altere la salida | baja | medio | `log_version` deja constancia en cada ejecución |
| R-4 | Se olvide una bandera de determinismo | media | alto | Van en el ejecutor; el llamador no las escribe |

---

## 9. Confianza global

- **Preguntas abiertas:** 1 — **1 BLOQUEANTE** (CA-8 / A-3)
- **Verificaciones cruzadas:**
  - [x] Precedente de HU-156 leído: una dependencia que abre rutas por dentro puede fallar en silencio
  - [x] `filesystem.system_path` y `find_executable` leídos en código
  - [x] Jerarquía de errores de HU-161 leída: mapea sin inventar nada
  - [x] Confirmado que el binario **no está instalado** (`ffmpeg -version` no responde)
- **Recomendación dividida:**
  - **Capa de construcción y validación** (CA-1 a CA-7): ✅ **LISTA** — es aritmética de
    cadenas y manejo de procesos, verificable sin el binario. **Confianza 88%.**
  - **Adopción de la cadena** (CA-8): ⛔ **BLOQUEADA. Confianza 0%** — la validación que el
    backlog exige literalmente no se ha ejecutado.
- **Consecuencia:** ADR-006 queda **Propuesto**. Ninguna HU de E5 que **ejecute** video puede
  cerrarse hasta que CA-8 pase en verde.

---

## 10. Dependencias
| ID | Relación | Estado |
|----|----------|--------|
| HU-150, HU-010, HU-156, HU-161 | Esqueleto, capa de filesystem, rastro, errores | DONE |
| HU-003, HU-014, HU-100–112, HU-167 | Dependen de este ADR | backlog — **bloqueadas por CA-8** |

---

## 11. Historial de cambios
| Fecha | Cambio | Por |
|-------|--------|-----|
| 2026-09-05 | Creación **retroactiva** tras la auditoría de gobernanza que detectó su ausencia | Claude (ejecutor) |
