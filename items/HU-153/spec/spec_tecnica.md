# Spec Técnica `HU-153` — `ADR Catálogo local: manifiestos JSON vs SQLite`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 93% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** cerrar el último ADR de stack pendiente — cómo se persiste el catálogo
  local de medios.
- **Para quién:** HU-012 (persistencia), HU-013 (re-ingesta idempotente), HU-018 (reporte),
  HU-035 (reportes de calidad), HU-057 (sidecar de transformaciones).
- **Módulo / dominio:** plataforma (E7) — el artefacto es `ADR-003`; la implementación es
  de HU-012.
- **No obvio (lo crítico que el ticket no dice de frente):** el criterio decisivo no es
  rendimiento ni consultas, sino **reproducibilidad byte a byte**, que el charter eleva a
  KPI verificado en CI con golden tests. Y ahí hay un dato medido, no intuido: **SQLite
  produce archivos distintos ante el mismo contenido** si cambia el orden de inserción o si
  el catálogo se construye de forma incremental (verificado en §9). Un golden test sobre el
  catálogo fallaría en cada re-ingesta aunque el contenido fuera idéntico.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- `docs/blueprint/adr/ADR-003-catalogo-local.md`: contexto, opciones comparadas contra las
  restricciones del charter, **evidencia empírica de determinismo**, decisión, consecuencias.
- Estado `Propuesto` → `Aceptado` al integrar (patrón de ADR-001/002).

### 2.2 OUT — NO entra (delimitaciones)
- Implementar la persistencia, la escritura atómica y el esquema de campos → **HU-012**.
- Re-ingesta idempotente → HU-013 · Reporte de inventario → HU-018.
- Sidecar de transformaciones → HU-057 (consumirá la misma decisión).
- Índices, consultas o migraciones de esquema → no aplican hasta que HU-012 defina campos.

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | El catálogo debe poder consultarse sin ejecutar nuestro código | Es requisito explícito de la constitución | CLAUDE.md (Esquema de Datos) |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- ¿Un manifiesto por lote o uno por asset? → P-1. · ¿Cuándo se reconsidera? → P-2.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `docs/blueprint/adr/ADR-003-catalogo-local.md` | nuevo | bajo | ✅ existen ADR-001 y ADR-002; convención vigente |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| Formato y ciclo de ADR-001/002 | Sí | Misma estructura y ratificación por integración |
| `json` y `sqlite3` (stdlib) | Sí (ambas opciones) | **Ninguna de las dos opciones añade dependencia**: el criterio de "menos dependencias" no desempata |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| N/A — HU documental; el esquema del catálogo lo define HU-012 | — | — | N/A |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "misma entrada + mismo perfil ⇒ misma salida, **byte a byte donde el formato lo permita**" · KPI "verificado en CI con golden tests" | charter §6.1, §7 | No | El formato del catálogo **debe permitirlo**: es el criterio dominante |
| RN-2 | "el catálogo […] **siempre cabe consultarlo con las herramientas del repo**" | CLAUDE.md | No | Legible y diffable sin herramienta externa ni cliente de base de datos |
| RN-3 | "Re-ingesta idempotente: mismo input no duplica ni reprocesa" | backlog HU-013 | No | Reejecutar sobre el mismo lote debe producir un catálogo **idéntico**, no equivalente |
| RN-4 | "sidecar **auditable**" | backlog HU-057 | No | El historial debe poder leerse y revisarse a mano |
| RN-5 | Prohibidos formatos que ejecuten código o requieran cargador seguro | `python.md` | No | Descarta pickle y YAML sin `SafeLoader` |
| RN-6 | Escala real: decenas–cientos de assets por lote | Maestro §8.2 | No | Las ventajas de índices y consultas de SQL no se activan a esta escala |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | El formato elegido produce bytes idénticos ante el mismo contenido lógico, sin importar el orden de construcción | **Verificado empíricamente antes de decidir** (§9) |

---

## 6. Preguntas abiertas

### P-1 — ¿Un manifiesto por lote o uno por asset?
- **Categoría:** INFORMATIVA (la decide HU-012 al definir el esquema)
- **Mi mejor hipótesis:** uno por lote para el catálogo, más sidecars por asset para el
  historial de transformaciones (HU-057 pide explícitamente "sidecar"). Un archivo por
  asset como catálogo haría ilegible el inventario completo.
- **Si se asume mal, costo:** reorganizar la escritura en HU-012, sin cambiar el formato.
- **Estado:** ABIERTA (transferida a HU-012)

### P-2 — ¿Bajo qué condición se reconsideraría SQLite?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** si aparecen lotes de decenas de miles de assets, consultas
  analíticas cruzadas entre lotes, o acceso concurrente de varios procesos. Ninguna está en
  el backlog v1. Conviene dejarlo escrito en el ADR como disparador explícito.
- **Si se asume mal, costo:** un ADR nuevo que supersede a este (el mecanismo existe).
- **Estado:** ABIERTA

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | JSON con claves ordenadas, UTF-8 y `ensure_ascii=False` como formato del catálogo | — | Re-generar catálogos (hoy no existe ninguno) |
| A-2 | Un manifiesto por lote; sidecars por asset para historial | P-1 | Reorganización en HU-012 |
| A-3 | El disparador de reconsideración queda escrito, no implementado | P-2 | ADR sucesor |
| A-4 | La escritura atómica (temp + rename) es viable en el sistema de archivos objetivo | — | HU-012 lo verificará al implementarlo |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | Lotes futuros mucho mayores hagan lento leer/escribir el manifiesto completo | rendimiento | baja | medio | Disparador de reconsideración escrito en el ADR; el formato JSON no impide migrar |
| R-2 | Pérdida del catálogo por escritura interrumpida | datos | media | alto | Escritura atómica (temp + rename) es requisito explícito de HU-012, no opcional |
| R-3 | Elegir por intuición un formato que rompa el KPI de reproducibilidad | proceso | **se materializó y se evitó** | alto | Se midió antes de decidir: la intuición inicial (que SQLite sería determinista) resultó **falsa en el caso realista** |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (2 INFORMATIVAS)
- **Asunciones tomadas:** 4
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop 8461c0d`: sin persistencia todavía; 167 tests verdes)
  - [x] Consumidores de la decisión cruzados en el backlog (HU-012/013/018/035/057)
  - [x] **Determinismo medido, no asumido** (sqlite3 3.45.3, ejecutado en la máquina real):

    | Escenario | SQLite | JSON con claves ordenadas |
    |---|---|---|
    | Mismo contenido, mismo orden de inserción | idéntico | idéntico |
    | Mismo contenido, **orden de inserción distinto** | **distinto** | idéntico |
    | Mismo contenido, **construido incrementalmente** | **distinto** | idéntico |

  - [x] Dependencias comparadas: ambas opciones son stdlib ⇒ ese criterio no desempata
  - [x] Escala real cruzada con el caso de uso (43 fotos en la auditoría del cliente 0)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 93% — el 7%: P-1/P-2, ambas de implementación o futuro, sin efecto en la decisión de formato.

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-150 | Esqueleto del repo | DONE |
| HU-012, HU-013, HU-018, HU-035, HU-057 | Consumen la decisión | backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna.

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — El ADR existe y decide
- **Then:** existe `docs/blueprint/adr/ADR-003-catalogo-local.md` con contexto, ≥2 opciones comparadas contra las restricciones del charter, decisión única y consecuencias

### CA-2 — La decisión se apoya en evidencia, no en opinión
- **Then:** el ADR incluye la tabla de determinismo medida en la máquina real, con la versión de SQLite usada

### CA-3 — El criterio dominante queda explícito
- **Then:** el ADR nombra la reproducibilidad byte a byte como razón principal y explica por qué los criterios habituales (rendimiento, consultas, dependencias) no desempatan aquí

### CA-4 — Queda escrito cuándo reconsiderar
- **Then:** el ADR lista los disparadores concretos que justificarían un ADR sucesor

### CA-5 — Convención de ADRs respetada
- **Then:** mismo formato y ciclo `Propuesto → Aceptado` que ADR-001 y ADR-002

### CA-6 — Trazabilidad
- **Then:** gate-log con `draft`, `gate_spec`, `dev` de HU-153

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial, medición de determinismo y evaluación de gate | Claude (ejecutor) |
