# HU-153 — Artefactos de DEV

| Artefacto | Ubicación | Estado |
|---|---|---|
| ADR-003 — Catálogo local: **manifiestos JSON con claves ordenadas** | `docs/blueprint/adr/ADR-003-catalogo-local.md` | Propuesto — se ratifica al integrar |

Con este ADR quedan **cerrados los tres ADRs de stack** que el proyecto arrastraba desde
Fase 0: entorno (uv), visión (opencv-headless + numpy) y catálogo (JSON).

**Lo que decidió el ADR fue una medición, no una preferencia.** La intuición de partida era
que SQLite sería determinista por ser un formato binario estable. Se midió antes de escribir
la decisión y resultó falso en el escenario que importa:

| Escenario | SQLite 3.45.3 | JSON con claves ordenadas |
|---|---|---|
| Mismo contenido, mismo orden | idéntico | idéntico |
| Mismo contenido, **otro orden de inserción** | **distinto** | idéntico |
| Mismo contenido, **construido incrementalmente** | **distinto** | idéntico |

Los dos casos divergentes son exactamente los que produce una re-ingesta, así que un golden
test sobre el catálogo habría fallado en cada corrida con contenido idéntico — rompiendo el
KPI de reproducibilidad del charter.

El ADR deja además **disparadores explícitos** para reconsiderar (lotes de decenas de miles,
consultas cruzadas entre lotes, acceso concurrente), de modo que la decisión sea revisable
con un criterio y no por opinión.
