# ADR-001 — Gestor de entorno y dependencias: uv

- **Estado:** Propuesto — se ratifica como *Aceptado* con el merge de `feature/HU-151-adr-entorno`
- **Fecha:** 2026-07-26
- **Origen:** HU-151 (backlog E7) · spec en `items/HU-151/spec/spec_tecnica.md`
- **Decisores:** equipo técnico (@oscardacto) · análisis: Claude (orquestador-ejecutor ASDD)

> Primer ADR del proyecto — fija también la convención: los ADRs viven en
> `docs/blueprint/adr/ADR-NNN-slug.md` con las secciones Contexto / Opciones /
> Decisión / Consecuencias, y su estado se actualiza en este encabezado.

---

## Contexto

media-optimizer exige **reproducibilidad 100%** (charter §7): los golden tests comparan
salida a nivel de píxel, y un cambio de versión de OpenCV/NumPy altera esa salida. El
entorno mismo es parte del determinismo — no basta fijar semillas si cada máquina
resuelve versiones distintas de las dependencias.

Restricciones aplicables: Python 3.12+ (stack), CPU-only, todo local (charter §6), y la
regla de gobernanza "no instalar dependencias de stack sin su ADR" (CLAUDE.md).

Entorno real verificado en la máquina de referencia (2026-07-26, Windows 10 Pro 19045):

| Hecho | Valor |
|---|---|
| Pythons instalados (`py -0p`) | **solo 3.13.2** (`%LOCALAPPDATA%\Programs\Python\Python313`) |
| `python` / `pip` en PATH | **no** — solo el launcher `py` |
| pip como módulo | `py -m pip` → pip 25.0.1 ✅ |
| `uv`, `winget`, `scoop` | no instalados |

Consecuencia directa: los comandos aspiracionales de CLAUDE.md (`python -m venv …`)
**fallan tal como están escritos** en la máquina de referencia.

## Opciones consideradas

### A — venv + pip (stdlib pura)
- ✅ Cero herramientas nuevas; funciona hoy con `py -m venv`; conocida por todos.
- ⚠️ **Sin lockfile**: `pip freeze` plano no registra hashes ni markers por plataforma —
  la reproducibilidad del entorno queda en "mejor esfuerzo", violando el criterio
  dominante. Resolución lenta. No gestiona versiones de Python.
- 📊 Riesgo directo sobre el KPI de reproducibilidad y los golden tests.

### B — venv + pip + pip-tools (`pip-compile` → lock)
- ✅ Lockfile con hashes; ecosistema pip estándar.
- ⚠️ Ya implica instalar una herramienta extra (mismo costo de aprobación que uv) pero
  sin sus beneficios: dos herramientas coordinadas a mano, lock por plataforma (el lock
  compilado en Windows no sirve tal cual en Linux), sin gestión de versiones de Python,
  velocidad pip.
- 📊 Punto medio que paga el precio de ambos mundos.

### C — uv (Astral)
- ✅ `uv.lock` **multiplataforma y con hashes** — reproducibilidad del entorno de serie.
  Gestiona versiones de Python (`uv python pin 3.12` mitiga el riesgo de wheels de
  OpenCV en 3.13 — R-1 de la spec). `uv run` no depende del PATH (irrelevante que
  `python`/`pip` no estén). Resolución e instalación 10–100× más rápidas que pip —
  relevante para el smoke E2E < 60 s en CI (HU-185). Binario único, sin runtime propio.
- ⚠️ Herramienta nueva para el equipo; proyecto externo (Astral) fuera de la stdlib;
  requiere instalación inicial (sin winget: instalador standalone o `py -m pip`).
- 📊 Una sola herramienta cubre entorno + dependencias + lock + versión de Python.

## Decisión

**uv** como gestor único de entorno, dependencias y versión de Python.

- `pyproject.toml` con `requires-python = ">=3.12"` (estándar — no acopla a uv).
- `uv.lock` **comiteado** al repo; `.python-version` fija la versión de desarrollo.
- La instalación efectiva de uv y la creación del proyecto ocurren en **HU-150**, ya con
  este ADR ratificado.

La razón dominante no es velocidad sino **determinismo**: es la única opción donde el
lockfile multiplataforma con hashes viene de serie, y el KPI de reproducibilidad 100%
lo exige. La familiaridad de venv+pip no compensa un entorno no reproducible; y si de
todos modos habría que aprobar una herramienta (pip-tools), uv domina esa comparación.

## Consecuencias

**Positivas**
- Golden tests corren sobre un entorno bit-a-bit idéntico entre máquinas y en el tiempo.
- HU-152 puede fijar la versión de Python por proyecto si OpenCV lo requiere, sin
  reinstalar nada a mano.
- Onboarding de una máquina nueva = instalar uv + `uv sync` (dos comandos).

**Negativas / mitigación**
- Curva de aprendizaje → tabla de equivalencias abajo; los comandos del día a día son 5.
- Dependencia de un tercero (Astral) → `pyproject.toml` es estándar PEP 621: cualquier
  máquina sin uv puede seguir instalando con `py -m pip install -e ".[dev]"` (sin lock).
  No hay lock-in de formato.

**Neutrales**
- Los comandos de CLAUDE.md se actualizan en HU-150, cuando dejen de ser aspiracionales.

## Comandos de referencia (máquina Windows de referencia)

Instalación de uv — sin winget/scoop, dos vías válidas (preferida la primera):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# alternativa, vía el pip verificado de la máquina:
py -m pip install --user uv
```

Día a día (equivalencias):

| Acción | uv | equivalente venv+pip |
|---|---|---|
| Crear/sincronizar entorno | `uv sync` | `py -m venv .venv` + activate + `pip install -e ".[dev]"` |
| Ejecutar tests | `uv run pytest` | activate + `pytest` |
| Agregar dependencia | `uv add opencv-python` | `pip install` + editar pyproject a mano |
| Regenerar lock | `uv lock` | (sin equivalente confiable) |
| Fijar versión de Python | `uv python pin 3.12` | reinstalar Python a mano |
