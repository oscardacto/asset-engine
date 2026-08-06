# Spec Técnica `HU-162` — `CLI base: entrypoint, versión, contexto y salida de errores`

> **Estado:** ✅ **LISTA PARA DEV** — P-1 cerrada por decisión de arquitectura (2026-08-06)
> **Fecha:** 2026-08-06
> **Confianza global:** 93% — ver sección 9
> **Diseño detallado:** [`diseno_cli.md`](diseno_cli.md) · **Decisión:** [`cierre_arquitectura_cli.md`](cierre_arquitectura_cli.md)

---

## 1. Resumen ejecutivo

- **Qué se pide:** el esqueleto de la CLI — punto de entrada, opciones globales, despacho a
  comandos, códigos de salida y traducción de errores. **No los comandos en sí.**
- **Para quién:** HU-017 y todas las HUs de comando que vengan detrás.
- **Módulo:** `media_optimizer.cli`.
- **Tecnología: `argparse` de la biblioteca estándar, con frontera tipada.** Decidido en
  **ADR-005** sobre medición reproducible. Cero dependencias nuevas.
- **No obvio:** el riesgo de esta HU no es el parseo, que es trivial. Es que **`argparse`
  devuelve un `Namespace` cuyos atributos son `Any`, y `mypy --strict` no ve nada dentro**
  — se midió: con un error de tipo deliberado reporta *"Success: no issues found"*. La
  frontera tipada resuelve el problema aguas abajo, pero **deja desprotegida la frontera
  misma**: si alguien añade una opción al parser y olvida el campo del dataclass, nada lo
  detecta. Esa es la deuda que esta HU tiene que cerrar con un test, no con disciplina.

---

## 2. Alcance

### 2.1 IN
- `main.py`: parser raíz, opciones globales, despacho, traducción de errores a códigos.
- `exit_codes.py`: `ExitCode` como `IntEnum`.
- `errors.py`: traducción `MediaOptimizerError` → mensaje accionable + código.
- `RunContext`: dataclass congelado con el contexto del run (workspace, perfil, log).
- Registro **explícito** de comandos (tupla, no descubrimiento dinámico).
- **Test de sincronía parser ↔ dataclass** — la mitigación que ADR-005 impone.
- Test de arquitectura: `argparse` solo dentro de `cli/`; `core/` no lo importa.

### 2.2 OUT
- **Los comandos** (`ingest`, etc.) → cada uno con su HU. Esta HU entrega el esqueleto y
  **un comando mínimo de prueba** que ejercita el despacho de punta a punta.
- **Cargar el perfil** → HU-130/131; aquí solo se recibe su nombre.
- **Configuración desde archivo** → HU-155.
- **Autocompletado de shell** → descartado en ADR-005; requeriría una dependencia.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Ejecutar sin comando | Ayuda + código `2`; nunca una traza |
| 2 | Comando inexistente | Mensaje de `argparse` + código `2` |
| 3 | `--workspace` en una ruta hostil (larga, nombre de dispositivo) | Va por la capa de ADR-004, como todo |
| 4 | Error del dominio | Mensaje accionable + su código; **sin stacktrace** |
| 5 | Excepción inesperada | **Se propaga con su traza**: es un bug, no un fallo esperable |
| 6 | `--log-file` en ruta hostil | `FilesystemFileHandler` de HU-156 |

---

## 3. Componentes

| Componente | Cambio | Verificado |
|---|---|---|
| `src/media_optimizer/cli/` (5 archivos + `commands/`) | nuevo | ✅ no existe en `develop` |
| `tests/cli/` | nuevo | ✅ no existe |
| `tests/test_arquitectura.py` | 2 reglas nuevas (A-2, A-4 de `arquitectura.md`) | ✅ leído |
| `pyproject.toml` | `[project.scripts]` para el entrypoint | ✅ leído: no existe la sección |

### 3.1 Reutilizables
| Componente | ¿Reutilizar? | Justificación |
|---|---|---|
| `core.errors` (HU-161) | **Sí** | La jerarquía ya distingue corrupto / inválido / bug; los códigos de salida se mapean 1 a 1 |
| `logs.configure_logging` (HU-156) | **Sí** | `--log-level` y `--log-file` son exactamente sus parámetros |
| `Workspace.ensure()` (HU-016) | **Sí** | `--workspace` construye uno |
| `ingest.filesystem` (HU-010) | **Sí, obligatorio** | Cualquier ruta que llegue por argumento |

---

## 4. Modelo de datos

Ver [`diseno_cli.md`](diseno_cli.md) §3 y §5. Resumen: un dataclass congelado por comando +
`RunContext` para lo global + `ExitCode` como `IntEnum`.

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|-------|--------|-------------|
| RN-1 | `argparse` y nada más | ADR-005 | Cero dependencias nuevas |
| RN-2 | `cli/` es capa delgada, cero lógica de negocio | `arquitectura.md` §3 | Un comando parsea, invoca y traduce |
| RN-3 | **`core/` nunca importa `argparse`** | `arquitectura.md` A-2 | Test de arquitectura |
| RN-4 | `argparse` solo dentro de `cli/` | `arquitectura.md` A-4 | Test de arquitectura |
| RN-5 | Cero `print()` | `python.md` · ruff `T20` | La consola se escribe por el escritor del comando |
| RN-6 | Un archivo corrupto degrada ese asset, no el lote | charter | Existe `ExitCode.PARTIAL` |
| RN-7 | Todo acceso a disco por la capa | ADR-004 | Las rutas de los argumentos también |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|-----------|----------|
| V-1 | Los `dest` del parser coinciden con los campos del dataclass | **test obligatorio** (ADR-005) |
| V-2 | Ningún módulo fuera de `cli/` importa `argparse` | test de arquitectura |
| V-3 | Un error del dominio no imprime traza | test |
| V-4 | Una excepción inesperada **sí** propaga su traza | test |
| V-5 | Cada código de salida se produce en su escenario | test por código |

---

## 6. Preguntas abiertas

### P-1 — ¿Qué superficie de comandos rige? — ✅ **CERRADA**
- **Decisión (2026-08-06):** **tres comandos — `run <etapa>`, `report <tipo>`, `label`.**
  Las etapas y los reportes son entradas de `pipeline/registry.py`, no comandos.
- **Razón:** ninguna de las dos superficies en discusión resolvía el defecto que la
  auditoría encontró — 6 HUs escritas como "reportes" sin decir cómo se invocan y 2 de
  corrección humana sin comando. Ambas derivaban los comandos de las etapas, y esas 8 HUs no
  son etapas. La decisión aplica a las etapas el principio que el charter §3 ya fijó para
  los perfiles.
- **Efecto sobre esta HU:** el registro de comandos es fijo y pequeño; lo que crece es el
  registro de `pipeline/`, que esta HU consume pero no define.
- **Sustento:** [`cierre_arquitectura_cli.md`](cierre_arquitectura_cli.md) §1 · migración
  ejecutada sobre 4 archivos, 0 cambios de alcance.

### P-3 — ¿Qué hace `run <etapa>` mientras el registro no tenga ejecutores?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** el registro declara la superficie completa desde el primer día
  (las 6 etapas y los 7 reportes ya están decididos), y cada entrada gana su ejecutor con su
  HU. Invocar una etapa sin ejecutor da un mensaje claro y sale con `FAILURE`. La
  alternativa —registro vacío que se va llenando— dejaría `run --help` mintiendo sobre lo
  que la herramienta va a poder hacer.
- **Estado:** ABIERTA (no bloquea)

### P-2 — ¿`--workspace` y `--profile` globales o por comando?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** globales. Son el contexto del run, no un parámetro de etapa;
  repetirlos obligaría al usuario a escribirlos dos veces al encadenar comandos.
- **Estado:** ABIERTA (no bloquea)

---

## 7. Asunciones

| # | Asunción | Costo si se rompe |
|---|----------|-------------------|
| A-1 | El contexto global va en el parser raíz (P-2) | Mover 4 argumentos |
| A-2 | 5 códigos de salida bastan | Añadir uno al enumerado, aditivo |
| A-3 | `[project.scripts]` de `pyproject.toml` como entrypoint | Alternativa: `python -m media_optimizer` |
| A-4 | La ayuda va en español y los nombres de comando en inglés | Reescribir cadenas |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|--------|-------|---------|------------|
| R-1 | **Parser y dataclass se desincronizan sin que nada lo detecte** | **alta** | alto | Test de sincronía por comando. **Es la única mitigación con evidencia objetiva y ADR-005 la impone** |
| R-2 | Se cuele lógica de negocio en un comando | media | alto | `arquitectura.md` §3 + revisión; el síntoma es un comando largo |
| R-3 | Implementar sobre la superficie equivocada (P-1) | **alta si no se resuelve** | **alto**: 6 HUs con enunciado falso | Bloquear el gate hasta decidir |
| R-4 | Una ruta hostil por argumento rompa el comando | baja | medio | Ya resuelto por ADR-004; test con ruta larga |

---

## 9. Confianza global

- **Preguntas abiertas:** 2 — **0 bloqueantes** (P-1 cerrada por decisión de arquitectura)
- **Verificaciones cruzadas:**
  - [x] ADR-005 aceptado, con la medición reproducible archivada
  - [x] `core/errors.py` leído: la jerarquía mapea a códigos de salida sin inventar nada
  - [x] `logs.configure_logging` leído: sus parámetros son los de `--log-level`/`--log-file`
  - [x] **Las 112 HUs auditadas una por una**; ninguna queda sin mecanismo de ejecución
  - [x] Superficie aprobada y migrada al backlog, la arquitectura y la documentación
  - [x] `pyproject.toml` leído: no hay `[project.scripts]`
- **Recomendación:** ✅ **LISTA PARA DEV.**
- **Confianza: 93%.** El 7% restante son P-3 (informativa) y R-1, que es el riesgo que la
  propia HU mitiga con el test de sincronía.

---

## 10. Dependencias
| ID | Relación | Estado |
|----|----------|--------|
| HU-150, HU-161, HU-156, HU-016, HU-010 | Esqueleto, errores, logs, workspace, filesystem | DONE |
| **ADR-005** | Fija la tecnología | **Aceptado** |
| HU-017, HU-037, HU-064, HU-078, HU-110, HU-184 | Colgarán de esta | backlog — **afectadas por P-1** |

---

## 11. Criterios de aceptación

- **CA-1** — `--version` imprime la versión y sale con `0`.
- **CA-2** — Sin comando: muestra la ayuda y sale con `2`, sin traza.
- **CA-3** — Comando inexistente: mensaje de uso y `2`.
- **CA-4** — Las opciones globales producen un `RunContext` con tipos verificados.
- **CA-5** — **Los `dest` del parser coinciden con los campos del dataclass**, por comando.
- **CA-6** — `mypy --strict` limpio sobre `cli/`.
- **CA-7** — Ningún módulo fuera de `cli/` importa `argparse`; `core/` tampoco.
- **CA-8** — Un `InvalidInputError` produce mensaje accionable y `3`, sin traza.
- **CA-9** — Una excepción inesperada **propaga su traza completa**.
- **CA-10** — Cada código de salida se produce en su escenario.
- **CA-11** — `--log-file` en ruta larga escribe bytes reales.
- **CA-12** — Cobertura ≥80% en `cli/` y batería verde.
- **CA-13** — Trazabilidad en el gate-log.

---

## 12. Historial de cambios
| Fecha | Cambio | Por |
|-------|--------|-----|
| 2026-08-06 | Creación tras aceptar ADR-005. Nace bloqueada por P-1 | Claude (ejecutor) |
