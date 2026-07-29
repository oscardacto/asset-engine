# ADR-003 — Catálogo local: manifiestos JSON con claves ordenadas

- **Estado:** Propuesto — se ratifica como *Aceptado* al integrar `feature/HU-153-adr-catalogo`
- **Fecha:** 2026-07-26
- **Origen:** HU-153 (backlog E7) · spec en `items/HU-153/spec/spec_tecnica.md`
- **Decisores:** equipo técnico (@oscardacto) · análisis: Claude (orquestador-ejecutor ASDD)

---

## Contexto

El catálogo guarda, por lote, qué assets se ingirieron y qué se sabe de cada uno
(dimensiones, hash, flags, veredicto, historial de transformaciones). No hay base de datos
externa: todo es local (charter §6.1).

Restricciones que aplican:

- **Reproducibilidad byte a byte**, elevada a KPI y *verificada en CI con golden tests*
  (charter §6.1 y §7).
- **Re-ingesta idempotente**: reejecutar sobre el mismo lote no debe duplicar ni reprocesar
  (backlog HU-013).
- El catálogo **debe poder consultarse con las herramientas del repo**, sin cliente externo
  (CLAUDE.md, Esquema de Datos), y el historial por asset debe ser un *sidecar auditable*
  (backlog HU-057).
- Escala real del caso de uso: decenas a cientos de assets por lote — la auditoría del
  cliente 0 cubre 43 fotos (Maestro §8.2).

Nota sobre dependencias: `json` y `sqlite3` están **ambos en la biblioteca estándar**, así
que el criterio de "menos dependencias" no desempata. Y `pickle`/YAML quedan descartados de
entrada por el checklist de seguridad de `.claude/rules/python.md`.

### Evidencia medida antes de decidir

La intuición de partida —"SQLite será determinista, es un formato binario estable"—
resultó **falsa en el escenario realista**. Medición ejecutada en la máquina de referencia
con **SQLite 3.45.3** (hash SHA-256 del archivo resultante):

| Escenario | SQLite | JSON con claves ordenadas |
|---|---|---|
| Mismo contenido, mismo orden de inserción | idéntico | idéntico |
| Mismo contenido, **orden de inserción distinto** | **distinto** | idéntico |
| Mismo contenido, **construido incrementalmente** (2 inserciones + 1) | **distinto** | idéntico |

Los dos escenarios en los que SQLite diverge son exactamente los que produce una
re-ingesta: el orden en que llegan los assets puede variar y el catálogo se actualiza de
forma incremental. Un golden test sobre el catálogo fallaría en cada corrida aunque el
contenido lógico fuera idéntico.

## Opciones consideradas

### A — Manifiestos JSON con claves ordenadas
- ✅ **Byte a byte reproducible** por construcción: mismo contenido lógico ⇒ mismo archivo,
  sin importar el orden de llegada ni si se construyó de una vez o por partes.
- ✅ Legible y *diffable* sin herramientas: cumple literalmente "consultable con las
  herramientas del repo"; un `git diff` muestra qué cambió entre corridas.
- ✅ Escritura atómica trivial (archivo temporal + `rename`).
- ⚠️ Lectura/escritura del manifiesto completo en cada actualización: irrelevante a la
  escala del caso de uso, costoso si algún día hay decenas de miles de assets.
- ⚠️ Sin índices ni consultas: filtrar exige cargar y recorrer en memoria.

### B — SQLite
- ✅ Consultas, índices y actualizaciones parciales; transacciones ACID; escala muy por
  encima de lo que este proyecto necesita.
- ⚠️ **Rompe el criterio dominante**: no reproducible byte a byte en los escenarios reales
  (evidencia arriba).
- ⚠️ Inspeccionarlo exige un cliente de SQL; no es *diffable* en git, lo que degrada la
  auditoría que el charter pide.
- ⚠️ Aporta capacidades (concurrencia, consultas analíticas) que ningún WorkItem del
  backlog v1 solicita.

### C — JSONL append-only
- ✅ Escrituras incrementales baratas; historial natural.
- ⚠️ La re-ingesta idempotente exigiría compactar el archivo, y la compactación reintroduce
  el problema de orden que se quería evitar. Además el estado actual de un asset requiere
  reconstruirse leyendo todo el historial.

## Decisión

**Manifiestos JSON con claves ordenadas** como formato del catálogo local.

- Serialización con `sort_keys=True`, `ensure_ascii=False`, UTF-8, indentado estable.
- Las colecciones se ordenan por una clave explícita del dominio (hash o ruta) antes de
  serializar: el orden es un dato, no un accidente de ejecución.
- Escritura atómica obligatoria (temporal + `rename`) — requisito de HU-012, no opcional.
- Un manifiesto por lote para el catálogo; sidecars por asset para el historial de
  transformaciones (HU-057).

La razón dominante es la **reproducibilidad byte a byte**: es KPI del proyecto y se
verifica en CI. Los criterios que normalmente decidirían esta elección —rendimiento,
consultas, concurrencia— no aplican a la escala real del caso de uso, y el criterio de
dependencias no desempata porque ambas opciones son stdlib.

## Consecuencias

**Positivas**
- Los golden tests pueden comparar el catálogo directamente, sin normalizaciones previas.
- `git diff` sobre un catálogo muestra exactamente qué cambió entre dos corridas: auditoría
  sin herramientas.
- La re-ingesta idempotente se vuelve verificable: mismo lote ⇒ archivo idéntico.

**Negativas / mitigación**
- Reescritura del manifiesto completo en cada actualización → aceptable a esta escala; si
  deja de serlo, ver disparadores abajo.
- Sin consultas nativas → los consumidores cargan y filtran en memoria, que es lo que ya
  hacen los módulos del dominio.

**Neutrales**
- El formato no impide migrar: un manifiesto JSON se importa a SQLite en un paso si algún
  día hace falta.

## Cuándo reconsiderar (disparadores de un ADR sucesor)

1. Lotes de **decenas de miles** de assets donde reescribir el manifiesto sea medible.
2. Consultas analíticas **cruzadas entre lotes** que exijan índices.
3. **Acceso concurrente** de varios procesos al mismo catálogo.

Ninguno está en el backlog v1. Si aparece alguno, el reemplazo se documenta en un ADR nuevo
que supersede a este, no modificando este.
