# Spec Técnica `HU-017` — `Etapa ingest (run ingest)`

> **Estado:** LISTA PARA DEV
> **Fecha:** 2026-08-06
> **Confianza global:** 92% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** la primera etapa real del registro: `run ingest <carpeta>` produce el
  catálogo en el workspace y un resumen en consola.
- **Módulo:** `media_optimizer.pipeline.stages` — la ejecución medida de etapas.
- **No obvio:** es una HU de **composición**: todas sus piezas existen y están cerradas
  (escaneo, triaje, medidas, hash, catálogo, workspace). Lo nuevo es (a) el ejecutor de
  etapa con su medición de tiempo y memoria —que pertenece a `pipeline/`, no a `core/`—,
  (b) la conexión con el comando `run` sin que `cli/` gane lógica, y (c) que la promesa
  no destructiva de HU-016 se **compruebe** en cada ejecución real, no solo en tests.

## 2. Alcance

### 2.1 IN
- `pipeline/stages.py`: `StageRequest`, `StageOutcome`, `execute_stage(name, request)` con
  medición (tiempo + memoria pico) que produce el `StageReport` de HU-168.
- Ejecutor de `ingest`: escaneo → triaje → medidas orientadas + hash → catálogo atómico en
  el workspace → verificación de originales intactos → resumen.
- Disponibilidad como dato derivado: una etapa está disponible si tiene ejecutor. El
  registro no puede decir "disponible" sin que exista el código, ni al revés.
- `cli/commands/run.py` invoca `execute_stage` y traduce el resultado a consola + código.

### 2.2 OUT
- El resumen tabular por asset → HU-018 (`report inventory`).
- `--force` / `--resume` con efecto real → HU-013 ya da la idempotencia; el cableado fino a
  la re-ingesta es de HU-182.
- Orquestador multi-etapa (`run all`) → HU-180/184.
- Video → E5.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Carpeta inexistente o que no es carpeta | `InvalidInputError` del escáner → código 3, mensaje accionable |
| 2 | `run ingest` sin carpeta | `InvalidInputError` propio: el origen es obligatorio para esta etapa |
| 3 | Lote con fotos corruptas | Cuarentena con causa; la etapa termina con código 4 (PARTIAL) |
| 4 | Lote perfecto | Código 0 |
| 5 | Un original cambia durante la ejecución | `MediaOptimizerError` → código 1: es integridad, no entrada |
| 6 | Workspace en ruta hostil | Ya cubierto por ADR-004/HU-016 |

## 3. Componentes

| Componente | Cambio |
|---|---|
| `src/media_optimizer/pipeline/stages.py` | nuevo |
| `src/media_optimizer/pipeline/registry.py` | `available` pasa a derivarse del ejecutor |
| `src/media_optimizer/cli/commands/run.py` | invoca la ejecución real |
| `tests/pipeline/test_stages.py` · `tests/cli/test_main.py` | nuevos/ampliados |

## 5. Reglas de negocio
| # | Regla | Implicación |
|---|-------|-------------|
| RN-1 | Observabilidad obligatoria (CLAUDE.md) | `execute_stage` mide y produce `StageReport`; se registra en el rastro |
| RN-2 | No destructivo comprobable (charter §6.3) | La huella de los orígenes se verifica tras escribir; los hashes ya calculados se reutilizan |
| RN-3 | Corrupto degrada, no tumba (charter) | Cuarentena + PARTIAL |
| RN-4 | `cli/` sin lógica (arquitectura §3) | El comando llama a una función y formatea |
| RN-5 | Determinismo (charter §6.1) | Todas las piezas compuestas ya lo garantizan; el catálogo es byte-idéntico entre corridas |

## 6. Preguntas abiertas
### P-1 — ¿Dónde se mide (tiempo/memoria)?
- INFORMATIVA. En `execute_stage`, una sola vez para todas las etapas futuras. `core/` sigue
  puro; medir es de la capa que orquesta (ya decidido en HU-168).

## 8. Riesgos
| # | Riesgo | Mitigación |
|---|--------|------------|
| R-1 | `available` en el registro y el ejecutor se desincronicen | La disponibilidad se **deriva** del ejecutor; test que lo verifica |
| R-2 | El resumen en consola se vuelva no determinista | Solo cuenta y ordena datos ya ordenados; test |

## 9. Confianza global
- **Preguntas abiertas:** 1 — 0 bloqueantes
- Verificado en código: firmas de las 8 piezas a componer, leídas una a una.
- **Confianza: 92%.** ✅ LISTA PARA DEV

## 11. Criterios de aceptación
- **CA-1** — `run ingest <carpeta>` produce `catalog.json` en el workspace, byte-idéntico entre dos corridas.
- **CA-2** — El resumen dice: encontrados, aceptados, apartados por causa, duplicados.
- **CA-3** — Lote limpio ⇒ código 0; con cuarentena ⇒ código 4; carpeta inválida ⇒ 3; sin carpeta ⇒ 3.
- **CA-4** — Los originales quedan intactos y **se comprueba** (huella reutilizando hashes).
- **CA-5** — La ejecución produce un `StageReport` con tiempo y memoria, registrado en el rastro.
- **CA-6** — La disponibilidad de la etapa se deriva del ejecutor: no pueden divergir.
- **CA-7** — Las medidas del catálogo son las orientadas (EXIF aplicado).
- **CA-8** — Gobernanza verde: `cli/` sigue sin lógica ni listas copiadas; todo IO por la capa.
- **CA-9** — Cobertura ≥80% del módulo nuevo y batería verde.
- **CA-10** — Trazabilidad en el gate-log.
