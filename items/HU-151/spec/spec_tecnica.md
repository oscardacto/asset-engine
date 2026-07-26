# Spec Técnica `HU-151` — `ADR Gestor de entorno y dependencias (venv+pip vs uv)`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 92% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** decidir y documentar en un ADR el gestor de entorno y dependencias
  del proyecto (venv+pip vs uv), antes de que HU-150 monte el esqueleto que depende de él.
- **Para quién:** el equipo técnico (consumidor directo: HU-150 `pyproject.toml` + layout).
- **Módulo / dominio:** plataforma (E7) — sin código de producto; el artefacto es
  `docs/blueprint/adr/ADR-001-gestor-entorno.md` (primer ADR: fija también la convención
  de ubicación y formato de ADRs).
- **No obvio (lo crítico que el ticket no dice de frente):** la decisión no es de gusto —
  el KPI de reproducibilidad 100% (charter §7) exige entorno reproducible, y eso convierte
  el **lockfile** en el criterio dominante, por encima de velocidad o familiaridad.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- Análisis comparativo de los enfoques (venv+pip · venv+pip+pip-tools · uv) contra las
  restricciones del charter §6 y el entorno real de la máquina de referencia.
- Redacción de `ADR-001` con contexto, opciones, decisión, consecuencias y comandos de
  referencia para HU-150 — estado **Propuesto**; se ratifica con el merge de esta HU.
- Creación de la convención de ADRs: directorio `docs/blueprint/adr/`, numeración
  `ADR-NNN-slug.md`, secciones estándar.

### 2.2 OUT — NO entra (delimitaciones)
- Crear `pyproject.toml`, lockfile o esqueleto del repo → **HU-150**.
- Instalar la herramienta elegida en la máquina → primer paso de **HU-150**, ya con el
  ADR ratificado (regla CLAUDE.md: no instalar dependencias de stack sin su ADR).
- Actualizar los comandos de `.claude/CLAUDE.md` → HU-150, cuando los comandos sean reales.
- ADRs de OpenCV (HU-152), catálogo (HU-153) y video (HU-154).

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | La decisión debe cerrarse antes de cualquier HU dependiente | HU-150 no arranca sin ADR-001 ratificado | backlog, reglas (`ADR` cierra decisión antes de dependiente) |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- Ratificación de instalar una herramienta nueva (uv) en la máquina → P-1.
- Portabilidad del lockfile si mañana hay CI en Linux → P-2.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `docs/blueprint/adr/ADR-001-gestor-entorno.md` | nuevo | bajo | ✅ no existe `docs/blueprint/adr/` — este ADR crea la convención |
| `items/HU-151/` (ESTADO, insumos, spec, dev) | nuevo | bajo | ✅ creado en DRAFT |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| Ninguno — el repo no tiene código ni ADRs previos (verificado con glob/grep en main) | N/A | Primer ADR del proyecto |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| N/A — HU documental, sin datos | — | — | N/A |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "Local y determinista … misma entrada + mismo perfil ⇒ misma salida" · KPI "Reproducibilidad 100% … golden tests" | charter §6.1, §7 | No | Las versiones de OpenCV/NumPy alteran la salida a nivel de píxel ⇒ el entorno mismo debe ser reproducible ⇒ **lockfile con hashes obligatorio** |
| RN-2 | "Las HUs marcadas `ADR` cierran una decisión de stack antes de que otra HU dependa de ella" | backlog, reglas | No | ADR-001 ratificado es precondición de HU-150 |
| RN-3 | "No instalar dependencias nuevas sin aprobación — y si son de stack, con su ADR" | CLAUDE.md, Modo de Operación | No | Este ADR **es** el mecanismo de aprobación; la instalación efectiva ocurre en HU-150 |
| RN-4 | "Python 3.12+" | CLAUDE.md, stack | No | La herramienta debe operar con 3.12+; ideal si además puede **fijar** la versión de Python por proyecto |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | Los comandos que el ADR documente deben ser ejecutables en la máquina de referencia (Windows 10, sin `python`/`pip` en PATH) | El ADR queda decorativo: HU-150 tropieza con el primer comando |

---

## 6. Preguntas abiertas

### P-1 — ¿El equipo ratifica instalar `uv` como herramienta de desarrollo en la máquina?
- **Categoría:** IMPORTANTE (no bloqueante: el ADR es la propuesta; se ratifica al aprobar el merge de esta HU — aprobar PRs es humano, fuera de mi autoridad)
- **Importa porque:** decide el primer paso de HU-150 (instalar uv vs crear venv con `py`).
- **Va dirigida a:** equipo técnico (@oscardacto).
- **Mi mejor hipótesis:** sí — la evidencia de §5/§8 y el análisis del ADR favorecen uv.
- **Si se asume mal, costo:** bajo y reversible — reescribir ADR-001 a "venv+pip+pip-tools" y ajustar comandos; sin código construido encima todavía.
- **Estado:** ABIERTA (se cierra con el merge o el rechazo del PR de HU-151)

### P-2 — ¿Habrá CI fuera de esta máquina Windows (p. ej. Linux) en v1?
- **Categoría:** INFORMATIVA
- **Importa porque:** el lockfile debe ser multiplataforma para no bifurcar entornos.
- **Va dirigida a:** equipo técnico.
- **Mi mejor hipótesis:** v1 corre local en Windows; `uv.lock` es multiplataforma por diseño, así que la respuesta no cambia la decisión.
- **Si se asume mal, costo:** nulo con uv; con `pip freeze` plano sí habría rework.
- **Estado:** ABIERTA

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Python 3.13.2 (único instalado, **verificado**) es baseline dev válido; el proyecto declara `requires-python = ">=3.12"` | — | Bajo — la herramienta elegida puede instalar/fijar otra versión |
| A-2 | Hay red disponible en fase de *setup* (instalar herramienta y descargar wheels); el principio "local, sin nube" del charter aplica al procesamiento de medios, no a la gestión de dependencias | — | Nulo — sin red no se instala nada con ninguna de las opciones |
| A-3 | Sin winget ni scoop (**verificado**), la instalación de uv usa el instalador standalone de Astral o `py -m pip install uv` (pip 25.0.1 **verificado**) | P-1 | Bajo — cambiar de método de instalación es trivial |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | Wheels de OpenCV incompatibles con Python 3.13 en Windows | técnico | baja | medio | Se verifica en HU-152; si pasa, la herramienta debe poder fijar 3.12 por proyecto (uv: `uv python pin`; venv: reinstalar otro Python a mano) |
| R-2 | Herramienta nueva (uv) desconocida para el equipo | cronograma | media | bajo | ADR documenta los 5 comandos del día a día; equivalencias pip anotadas |
| R-3 | Credencial de GitHub en la máquina pertenece a otra cuenta (`mipressyasta`) — bloquea push/PR del flujo de ramas | proceso | alta (ya ocurrió) | medio | Re-autenticar como `oscardacto` (en curso); no afecta el contenido del ADR |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (1 IMPORTANTE, 1 INFORMATIVA)
- **Asunciones tomadas:** 3 (dos respaldadas por verificación directa en la máquina)
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído y cruzado (repo sin código; charter, backlog, CLAUDE.md, rules leídos)
  - [x] Rama principal de los componentes relevantes leída (`docs/blueprint/` en `main`; no existe `docs/blueprint/adr/`)
  - [x] Esquema/API real cruzado — aquí, el **entorno real**: `py -0p` → solo 3.13.2 · `python`/`pip`/`uv` fuera de PATH · `py -m pip` = pip 25.0.1 · sin winget/scoop · Windows 10 Pro 19045
  - [x] Componentes "reutilizables" en §3.1 buscados, no asumidos (glob `docs/**`, grep ADR)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 92% — el 8% restante: ratificación pendiente (P-1) y el riesgo R-1, ninguno bloqueante para redactar el ADR.

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-150 | Consume esta decisión (pyproject, lockfile, comandos) | pendiente en backlog |
| HU-152 | Su ADR de OpenCV puede forzar `uv python pin 3.12` (R-1) | pendiente en backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna.

### 10.3 Servicios o equipos externos
- GitHub (`oscardacto/asset-engine`) para el flujo de PR — bloqueado por credencial (R-3), no bloquea DEV local.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — El ADR existe y decide
- **Given:** un repo sin ADRs ni convención de ADRs
- **When:** HU-151 completa DEV
- **Then:** existe `docs/blueprint/adr/ADR-001-gestor-entorno.md` con contexto, ≥2 opciones comparadas contra las restricciones del charter, decisión única explícita, consecuencias y estado (`Propuesto` → `Aceptado` al merge)

### CA-2 — Los comandos son reales, no aspiracionales
- **Given:** la máquina de referencia (Windows 10, solo `py` en PATH, sin winget)
- **When:** se leen los comandos de instalación y uso diario del ADR
- **Then:** cada comando es ejecutable en esa máquina tal como está escrito (método de instalación incluido), sin depender de `python`/`pip` en PATH

### CA-3 — La decisión sirve el KPI de reproducibilidad
- **Given:** el KPI "Reproducibilidad 100%" (charter §7)
- **When:** se aplica la decisión en HU-150
- **Then:** el mecanismo elegido produce un lockfile versionable con hashes que fija todas las dependencias transitivas, multiplataforma

### CA-4 — Trazabilidad del ciclo
- **Given:** el gate-log del proyecto
- **When:** HU-151 pasa por DRAFT→SPEC→DEV
- **Then:** `items/_metrics/gate-log.jsonl` registra `draft`, `gate_spec` (con confianza y conteos) y `dev`

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial, verificaciones de entorno y evaluación de gate | Claude (ejecutor) |
| 2026-07-26 | DEV: ADR-001 redactado (decisión: uv; estado Propuesto) en `docs/blueprint/adr/` — crea la convención de ADRs. Sin desviaciones respecto a §2 | Claude (ejecutor) |
