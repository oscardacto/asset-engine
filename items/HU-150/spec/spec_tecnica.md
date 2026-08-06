# Spec Técnica `HU-150` — `Esqueleto del repo: pyproject, layout src/, ruff+mypy+pytest`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 90% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** montar el esqueleto ejecutable del repo — instalación de uv (ADR-001),
  `pyproject.toml`, layout `src/`, lockfile, y ruff+mypy+pytest configurados con los
  límites de `.claude/rules/python.md` como configuración, no como prosa.
- **Para quién:** todas las HUs siguientes de E7/E1/E2 — es la segunda HU del orden de
  arranque y casi todo depende de ella.
- **Módulo / dominio:** plataforma (E7). Primer código versionado del proyecto.
- **No obvio (lo crítico que el ticket no dice de frente):** el esqueleto NO pre-crea los
  9 módulos de la arquitectura como carpetas vacías — cada módulo nace con su primera HU
  (filosofía ADR-005 del template citada en CLAUDE.md: ninguna abstracción sin una
  implementación real que la necesite). El esqueleto entrega el paquete raíz + tooling.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- Instalación de uv en la máquina de referencia (autorizada por ADR-001 **Aceptado**).
- `pyproject.toml`: metadatos PEP 621 (`requires-python = ">=3.12"`, sin dependencias de
  runtime), grupo dev (pytest, pytest-cov, ruff, mypy), build backend hatchling.
- Configuración de tooling que materializa `python.md`: ruff (C901≤10, `max-args=5`,
  reglas `S` de seguridad, `PTH` pathlib, `T20` sin print, formato), mypy estricto sobre
  `src/`, pytest con `tests/`.
- Layout: `src/media_optimizer/__init__.py` (con `__version__`) + `py.typed` ·
  `tests/test_smoke.py` · `.python-version` · `uv.lock` comiteado.
- Verificación en verde de los 4 comandos: `uv sync` · `uv run pytest` ·
  `uv run ruff check .` + `format --check` · `uv run mypy src/`.

### 2.2 OUT — NO entra (delimitaciones)
- Subpaquetes de la arquitectura (`core/`, `vision/`, …) → nacen con HU-157+ (cada módulo
  con su primera HU).
- CLI (HU-162) — por eso el esqueleto no tiene dependencias de runtime.
  > **Nota posterior (2026-08-06):** esta linea decia 'CLI Typer'. ADR-005 fijo `argparse`
  > de la stdlib sobre medicion; la conclusion de la spec no cambia — sigue sin haber
  > dependencias de runtime, y ahora tampoco las habra.
- Pre-commit con ruff+mypy+pytest dirigido (HU-163) · benchmarks (HU-165) · logging
  (HU-156) · config externalizada (HU-155) · fixtures (HU-166).
- Actualizar los comandos de CLAUDE.md y el flujo de ramas → propuesta de gobernanza
  separada (ya anotada en feedback de HU-151); no se mezcla con esta HU.

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | "configurados con los límites de `python.md`" | Los límites entran como config ejecutable de ruff donde ruff pueda medirlos | backlog HU-150 |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- No todos los límites de `python.md` son medibles por ruff (módulo≤300/clase≤200/función≤40
  líneas no tienen regla nativa) → se documenta qué queda en disciplina de revisión → P-2.
- Nombre del paquete vs nombre del repo GitHub → P-1.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| uv (herramienta, máquina de referencia) | instalación | bajo | ✅ NO instalado (verificado 2026-07-26); ADR-001 Aceptado autoriza |
| `pyproject.toml` · `uv.lock` · `.python-version` | nuevo | bajo | ✅ no existen en `develop` |
| `src/media_optimizer/` (`__init__.py`, `py.typed`) | nuevo | bajo | ✅ no existe `src/` |
| `tests/test_smoke.py` | nuevo | bajo | ✅ no existe `tests/` |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| `.gitignore` (ya cubre `.venv/`, caches de pytest/mypy/ruff) | Sí | El esqueleto no necesita tocar las secciones de build |
| ADR-001 §Comandos | Sí | Los comandos de instalación/uso ya están verificados contra la máquina |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| N/A — sin datos de dominio todavía | — | — | N/A |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "uv como gestor único … `uv.lock` comiteado; `.python-version` fija la versión" | ADR-001 §Decisión | No | `uv sync` genera el lock; ambos van al repo |
| RN-2 | Límites: C901≤10, ≤5 parámetros, reglas S, pathlib, sin print | `python.md` | No | `[tool.ruff.lint]`: `mccabe.max-complexity=10`, `pylint.max-args=5`, select incluye `S`, `PTH`, `T20` |
| RN-3 | "mypy estricto" + "tipado completo" | CLAUDE.md stack · `python.md` | No | `[tool.mypy] strict = true` desde el día cero (activarlo después es rework) |
| RN-4 | "Python 3.12+" | CLAUDE.md stack | No | `requires-python = ">=3.12"`; dev fijado a 3.13 (único instalado, verificado) |
| RN-5 | "cada commit deja el proyecto compilable y con tests en verde" | CLAUDE.md, Modo de Operación | No | El esqueleto incluye un smoke test para que "verde" sea medible desde el primer commit |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | Los 4 comandos (`sync`/`pytest`/`ruff`/`mypy`) corren en verde en la máquina de referencia antes de comitear | La HU no pasa a QA — es su definición de esqueleto |
| V-2 | `uv.lock` contiene hashes y todas las transitivas | Viola RN-1/KPI reproducibilidad |

---

## 6. Preguntas abiertas

### P-1 — ¿El paquete se llama `media_optimizer` o `asset_engine`?
- **Categoría:** IMPORTANTE (no bloqueante — hay hipótesis fuerte y el costo de rename es bajo hoy)
- **Importa porque:** el repo GitHub se llama `asset-engine`, pero TODA la constitución
  (charter, backlog, CLAUDE.md) dice `media-optimizer`. El nombre de import se propaga a
  cada archivo futuro.
- **Va dirigida a:** @oscardacto.
- **Mi mejor hipótesis:** `media-optimizer` / `media_optimizer` — la constitución manda;
  el nombre del repo es hosting, no identidad del producto.
- **Si se asume mal, costo:** hoy, un rename de 3 archivos; tras 10 HUs, sed masivo + churn.
- **Estado:** ABIERTA (asunción A-1 la cubre)

### P-2 — ¿Aceptamos que los límites de líneas (módulo≤300/clase≤200/función≤40) queden en revisión, no en ruff?
- **Categoría:** INFORMATIVA
- **Importa porque:** ruff no tiene reglas nativas de conteo de líneas por módulo/clase/función; lo medible queda en config (C901, max-args) y lo demás en disciplina.
- **Mi mejor hipótesis:** sí — añadir un linter extra solo para contar líneas sería dependencia nueva sin ADR (violaría la propia regla).
- **Si se asume mal, costo:** nulo — puede añadirse después vía HU-163.
- **Estado:** ABIERTA

### P-3 — ¿`line-length` de ruff: 88 (default) o 100?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** 100 — código de visión con nombres descriptivos respira mejor; es el valor de facto en proyectos científicos.
- **Si se asume mal, costo:** un `ruff format` re-formatea todo; trivial hoy.
- **Estado:** ABIERTA

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Paquete = `media-optimizer` (dist) / `media_optimizer` (import), versión inicial `0.1.0` | P-1 | Rename de 3 archivos + uv.lock regenerado |
| A-2 | Límites no medibles por ruff quedan como disciplina de revisión (documentados en pyproject como comentario) | P-2 | Nulo — ampliable en HU-163 |
| A-3 | `line-length = 100` | P-3 | `ruff format` masivo (hoy: 2 archivos) |
| A-4 | El instalador standalone de Astral funciona con la execution policy actual; si no, fallback `py -m pip install --user uv` (pip 25.0.1 verificado) | — | Cambio de método, 1 comando |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | Instalador de uv bloqueado (red corporativa / execution policy) | técnico | baja | bajo | Fallback A-4 vía `py -m pip` |
| R-2 | uv instalado pero fuera del PATH de sesiones nuevas de la shell | técnico | media | bajo | Invocar por ruta completa (`%USERPROFILE%\.local\bin\uv.exe`) hasta reiniciar sesión |
| R-3 | Dev-deps con floors flotantes (`>=`) resuelven distinto en el futuro | datos/determinismo | media | nulo con lock | `uv.lock` fija exactas — el lock es la fuente de verdad, no los floors |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 3 total — **0 bloqueantes** (1 IMPORTANTE, 2 INFORMATIVAS)
- **Asunciones tomadas:** 4 (A-4 respaldada por verificación de pip)
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído y cruzado (`develop` sin `src/`, sin `pyproject`, sin `tests/`)
  - [x] Rama principal leída (topología `main`/`develop` verificada tras PR #1)
  - [x] Entorno real cruzado: Python 3.13.2 único · `py -m pip` 25.0.1 · uv/winget/scoop ausentes (re-verificado al cierre de HU-151, mismo día)
  - [x] Componentes reutilizables buscados (§3.1): .gitignore y ADR-001 §Comandos
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 90% — el 10%: P-1 (nombre) y R-1/R-2 (fricción de instalación), todos con mitigación barata.

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-151 / ADR-001 | Consume la decisión (uv, Aceptado vía PR #1) | DONE |
| HU-152, HU-153, HU-155–169 | Dependen de este esqueleto | backlog |

### 10.2 Datos/configuración previa requerida
- Acceso a red para descargar uv y los wheels dev (pytest/ruff/mypy) — fase de setup.

### 10.3 Servicios o equipos externos
- astral.sh (instalador) y PyPI (wheels) — solo durante la instalación/lock.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — uv instalado conforme al ADR
- **Given:** la máquina de referencia sin uv (verificado)
- **When:** se ejecuta el comando de instalación del ADR-001 (o su fallback)
- **Then:** `uv --version` responde

### CA-2 — Proyecto sincronizable y lockeado
- **Given:** `pyproject.toml` del esqueleto
- **When:** `uv sync`
- **Then:** se crea `.venv/` (ignorado por git) y `uv.lock` con hashes y transitivas; `pyproject.toml` + `uv.lock` + `.python-version` quedan comiteados

### CA-3 — Tests en verde
- **When:** `uv run pytest`
- **Then:** pasa el smoke test (importa `media_optimizer`, verifica `__version__`), exit 0

### CA-4 — Lint y formato limpios con los límites del estándar
- **When:** `uv run ruff check .` y `uv run ruff format --check .`
- **Then:** exit 0, y la config contiene C901=10, `max-args=5` y reglas `S` activas

### CA-5 — Tipado estricto limpio
- **When:** `uv run mypy src/`
- **Then:** exit 0 en modo `strict`

### CA-6 — Layout importable y tipado
- **Given:** `src/media_optimizer/` con `py.typed`
- **When:** `uv run python -c "import media_optimizer; print(media_optimizer.__version__)"`
- **Then:** imprime `0.1.0`

### CA-7 — Trazabilidad del ciclo
- **Then:** gate-log con `draft`, `gate_spec` y `dev` de HU-150

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial y evaluación de gate | Claude (ejecutor) |
| 2026-07-26 | DEV: uv 0.11.32 instalado (instalador Astral, R-1 no se materializó); esqueleto construido según §2.1 sin desviaciones; asunciones A-1 (media_optimizer) y A-3 (line-length 100) aplicadas; lock con ruff 0.16.0, mypy 2.3.0, pytest 9.1.1; batería CA-1…CA-6 en verde | Claude (ejecutor) |
