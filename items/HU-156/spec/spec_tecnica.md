# Spec Técnica `HU-156` — `Logging estructurado base`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-08-06
> **Confianza global:** 88% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** el mecanismo con el que todo el sistema deja rastro: una línea JSON por
  evento, con niveles, y cero `print()`.
- **Para quién:** HU-180 (orquestador), HU-183 (métricas JSONL), y los comandos de CLI.
- **Módulo:** `media_optimizer.logs` — nivel superior (ver P-1).
- **No obvio — la biblioteca estándar no sirve tal cual, y se midió.** `logging.FileHandler`
  normaliza la ruta con `os.path.abspath`, que es **la misma función que HU-010 demostró
  destructiva**. Sobre un archivo de log en una ruta larga falla; sobre `CON.log` levanta un
  `ValueError` incomprensible; y sobre `NUL.log` **no protesta y descarta todos los
  registros**, porque `abspath` la convierte en el dispositivo nulo. Un sistema de
  observabilidad que reporta éxito mientras tira cada línea es el peor fallo posible de esta
  HU: no deja señal de que falte algo.
- **Segundo hallazgo, de gobernanza:** el test de arquitectura de ADR-004 **no detecta**
  `logging.FileHandler(ruta)`. Vigila `open`, `os.*`, `shutil.*` y métodos de `Path`, pero
  no que una clase de terceros abra el archivo por dentro. Esta HU cierra ese hueco.

---

## 2. Alcance

### 2.1 IN
- `JsonLinesFormatter`: un registro por línea, JSON con **claves ordenadas** (ADR-003).
- `configure_logging(level, stream=None, log_file=None)`: configuración explícita, idempotente.
- `FilesystemFileHandler`: handler que pasa la ruta por la capa de ADR-004 antes de abrir.
- Campos estructurados por evento vía `extra={...}`, sin romper la línea JSON.
- **Ampliar `tests/test_arquitectura.py`** para que `logging.FileHandler` fuera de la capa
  sea una violación detectada.

### 2.2 OUT
- **Rotación de logs por tamaño o fecha** → sin HU asignada; se anota. `RotatingFileHandler`
  hereda el mismo defecto de `abspath` y tendría el mismo arreglo.
- **Métricas de run en JSONL** (HU-183) → usa este mecanismo, pero es otro archivo y otro
  esquema: las métricas son datos del run, no diagnóstico.
- **Configuración del nivel desde archivo** → HU-155.
- **Correlación por run-id** → nace con HU-180, que es quien conoce el run.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Ruta de log larga o con nombre de dispositivo | Pasa por la capa; **medido, no supuesto** |
| 2 | `configure_logging` llamado dos veces | Idempotente: no duplica handlers ni líneas |
| 3 | Un campo `extra` con un valor no serializable | Se representa como texto en vez de romper la línea |
| 4 | Un mensaje con acentos o emoji | `ensure_ascii=False` (ADR-003); se escribe en UTF-8 |
| 5 | Un campo `extra` que choca con uno reservado (`message`, `level`) | El reservado gana; el del llamador no puede falsear el nivel |

---

## 3. Componentes

| Componente | Cambio | Verificado |
|---|---|---|
| `src/media_optimizer/logs.py` | nuevo | ✅ no existe en `develop` |
| `tests/test_logs.py` | nuevo | ✅ no existe |
| `tests/test_arquitectura.py` | amplía la regla | ✅ leído: hoy no cubre `FileHandler` |
| `items/HU-156/dev/probe_filehandler.py` | evidencia de la medición | — |

### 3.1 Reutilizables
| Componente | ¿Reutilizar? | Justificación |
|---|---|---|
| `ingest.filesystem.system_path` (HU-010) | **Sí, obligatorio** | Es exactamente lo que le falta a `FileHandler`; medido que basta |
| `logging` de la stdlib | Sí, como base | Niveles, propagación y `extra` ya resueltos; lo único roto es cómo abre el archivo |
| Convención JSON de ADR-003 | Sí | `sort_keys=True`, `ensure_ascii=False` |

---

## 4. Modelo de datos

Una línea de log es un objeto JSON con claves ordenadas:

```json
{"asset": "IMG_0031.jpg", "level": "WARNING", "logger": "media_optimizer.ingest",
 "message": "EXIF ilegible, se continúa sin orientación", "timestamp": "2026-08-06T14:22:03.412Z"}
```

Los campos reservados (`timestamp`, `level`, `logger`, `message`) siempre están; el resto lo
pone el llamador con `extra`. **Las claves van ordenadas** para que dos líneas equivalentes
se lean y se comparen igual, aunque el conjunto de campos varíe entre eventos.

### 4.1 Por qué el log no es una salida comparable
Lleva marca de tiempo, así que **no** entra en golden tests — la misma tensión que resolvió
HU-168, y con la misma conclusión: no se disfraza de determinista. Lo que sí se verifica es
que **cada línea sea JSON válido y con las claves ordenadas**.

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|-------|--------|-------------|
| RN-1 | Cero `print()` en código de librería | `python.md` · ruff `T20` | Ya activo; esta HU da la alternativa |
| RN-2 | Todo acceso al disco por la capa | ADR-004 | El handler de archivo pasa por `system_path` |
| RN-3 | JSON con claves ordenadas y `ensure_ascii=False` | ADR-003 | Formatter propio |
| RN-4 | Un archivo corrupto degrada ese asset, no tumba el pipeline | `python.md` | Un `extra` no serializable no puede romper la línea |
| RN-5 | Cobertura ≥80% del módulo tocado | Pre-Flight | Evidencia al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|-----------|----------|
| V-1 | Cada línea emitida es JSON válido | test |
| V-2 | Las claves salen ordenadas | test |
| V-3 | Un log a ruta larga / `CON.log` / `NUL.log` **se escribe de verdad** | test que verifica bytes en disco, no ausencia de excepción |
| V-4 | Configurar dos veces no duplica líneas | test |
| V-5 | `logging.FileHandler` fuera de la capa es violación de arquitectura | test de gobernanza |

---

## 6. Preguntas abiertas

### P-1 — ¿Dónde vive el módulo?
- **Categoría:** IMPORTANTE (no bloqueante)
- **Mi mejor hipótesis:** `media_optimizer/logs.py`, nivel superior. La tabla de CLAUDE.md
  asigna la observabilidad a `pipeline/`, pero **el logging lo usan todas las capas**
  —incluida `ingest`, que es anterior a cualquier pipeline— y crear `pipeline/` ahora, con
  un solo archivo y sin su orquestador (HU-180), sería inventar estructura sin consumidor.
  Mismo criterio que ratificó `workspace` en HU-016.
- **Costo si se asume mal:** mover un archivo.
- **Estado:** ABIERTA (ratificable con la integración)

### P-2 — ¿El handler de archivo debe crear la carpeta que falte?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** **sí**, vía `filesystem.make_directory`. Que el primer intento de
  registrar algo falle porque la carpeta no existía es un fallo del sistema de diagnóstico
  justo cuando se lo necesita. `Workspace.ensure()` ya usa la misma función.
- **Estado:** ABIERTA

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|----------|-------------------|
| A-1 | `logs.py` a nivel superior (P-1) | Mover un archivo |
| A-2 | El handler crea la carpeta que falte (P-2) | Quitar dos líneas |
| A-3 | `logging` de la stdlib como base; lo único que hay que reemplazar es la apertura del archivo | **Medido**, no supuesto: con la ruta ya adaptada, `FileHandler` funciona en los 4 casos hostiles |
| A-4 | La rotación de logs no hace falta en v1 | Añadir un handler, aditivo |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R-1 | Los logs se pierden en silencio en una ruta hostil | **medida como real** | **alto** | Handler propio + test que comprueba **bytes en disco**, no ausencia de excepción |
| R-2 | Alguien use `logging.FileHandler` directo más adelante | media | alto (mismo fallo silencioso) | El test de arquitectura pasa a detectarlo |
| R-3 | Un `extra` no serializable rompa el run | media | medio | Se representa como texto; test explícito |
| R-4 | Configurar dos veces duplique cada línea | media | bajo | Idempotencia + test |

---

## 9. Confianza global

- **Preguntas abiertas:** 2 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] **Comportamiento de `logging.FileHandler` medido** sobre 4 rutas hostiles, en las dos
        variantes (tal cual / adaptada) — no supuesto
  - [x] Confirmado que el fallo de `NUL.log` es **silencioso**, comprobando bytes en disco
  - [x] `tests/test_arquitectura.py` leído: hoy no cubre handlers de terceros
  - [x] ADR-003 y ADR-004 leídos; regla `T20` verificada activa en `pyproject.toml`
  - [x] `filesystem.system_path` y `make_directory` leídos en código
- **Recomendación:** ✅ **LISTA PARA DEV**
- **Confianza: 88%.** El 12%: P-1 (ubicación, con implicación en la tabla de módulos) y R-3.

---

## 10. Dependencias
| ID | Relación | Estado |
|----|----------|--------|
| HU-150, HU-010, HU-016 | Esqueleto, capa de filesystem, `make_directory` | DONE |
| HU-155 | Configurará el nivel desde archivo | backlog |
| HU-180, HU-183 | Lo consumirán | backlog |

---

## 11. Criterios de aceptación

- **CA-1** — Cada registro emitido es una línea de JSON válido.
- **CA-2** — Las claves de cada línea salen ordenadas alfabéticamente.
- **CA-3** — Los campos `extra` del llamador aparecen en la línea junto a los reservados.
- **CA-4** — Un `extra` no serializable se representa como texto y **no** rompe la emisión.
- **CA-5** — Un `extra` que choca con un campo reservado no puede falsearlo.
- **CA-6** — Un log a un archivo en ruta larga **escribe bytes reales en disco**.
- **CA-7** — Un log a `CON.log` / `NUL.log` **escribe bytes reales en disco** (el caso que la stdlib pierde en silencio).
- **CA-8** — El handler crea la carpeta de destino si falta.
- **CA-9** — `configure_logging` dos veces no duplica líneas.
- **CA-10** — Los acentos se escriben tal cual, no escapados.
- **CA-11** — El test de arquitectura detecta `logging.FileHandler` fuera de la capa.
- **CA-12** — Cobertura ≥80% del módulo y batería verde.
- **CA-13** — Trazabilidad en el gate-log.

---

## 12. Historial de cambios
| Fecha | Cambio | Por |
|-------|--------|-----|
| 2026-08-06 | Creación, sobre medición previa del `FileHandler` de la stdlib | Claude (ejecutor) |
