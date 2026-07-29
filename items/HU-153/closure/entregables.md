# Entregables — HU-153

## Integración
| Merge | Repositorio | Rama | Descripción |
|-------|-------------|------|-------------|
| `9cb5d48` | oscardacto/asset-engine | `feature/HU-153-adr-catalogo` → `develop` | ADR-003 (catálogo JSON con claves ordenadas). Integrado por Claude; ratifica A-1 (formato) y deja P-1/P-2 transferidas a HU-012 |

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| Medición de determinismo (SQLite vs JSON, sqlite3 3.45.3) | Máquina de referencia | 2026-07-26 | ✅ ejecutada **antes** de decidir |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 El ADR existe y decide | `docs/blueprint/adr/ADR-003-catalogo-local.md` | contexto, ≥2 opciones vs charter, decisión única, consecuencias | ✅ 3 opciones (JSON / SQLite / JSONL), decisión: JSON con claves ordenadas | el propio archivo (`655a05b`) |
| CA-2 Decisión con evidencia | tabla de determinismo del ADR | medición real, con versión de SQLite | ✅ 3 escenarios medidos, SQLite 3.45.3 nombrada | ADR §Contexto |
| CA-3 Criterio dominante explícito | texto del ADR | nombra la reproducibilidad byte a byte y explica por qué los criterios habituales no desempatan | ✅ incluye la nota de que ambas opciones son stdlib | ADR §Contexto y §Decisión |
| CA-4 Cuándo reconsiderar | sección final del ADR | disparadores concretos | ✅ 3 disparadores (escala, consultas cruzadas, concurrencia) | ADR §Cuándo reconsiderar |
| CA-5 Convención respetada | comparación con ADR-001/002 | mismo formato y ciclo | ✅ Propuesto → Aceptado al integrar | los tres ADRs |
| CA-6 Trazabilidad | gate-log HU-153 | draft/gate_spec/dev | ✅ + qa/done de este cierre | gate-log.jsonl |

**Resultado: 6/6 criterios cumplidos · 0 fallidos · sin rework.**
Batería del proyecto sobre `develop` fusionado: **167 tests passed**, ruff limpio, mypy Success (HU documental — no añade código).

## Commits relevantes
- `f32fd4b` — HU-153 DRAFT+SPEC (93%, 0 bloqueantes) con la medición de determinismo
- `655a05b` — HU-153 DEV: ADR-003 + tabla de stack de CLAUDE.md sin filas pendientes
- `9cb5d48` — merge a `develop`
