# Spec Técnica `HU-005` — `Detección de orientación V/H (dimensiones + EXIF Orientation)`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 91% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** saber si una foto es vertical, horizontal o cuadrada, combinando sus
  medidas con la orientación declarada en el EXIF.
- **Para quién:** HU-018 (reporte), HU-059 (stories 9:16 desde verticales), HU-074
  (elegibilidad por formato de salida).
- **Módulo / dominio:** `media_optimizer.ingest` — módulo nuevo `orientation.py`.
- **No obvio:** la pregunta real no es "¿cómo se clasifica V/H?" —eso ya está resuelto en
  `core`— sino **cuál de las dos orientaciones es la verdadera**. HU-004 midió que OpenCV
  gira la imagen al abrirla si el EXIF lo pide, así que la misma foto es vertical leída de
  cabecera y horizontal ya abierta. Si el pipeline no elige explícitamente, el reporte de
  inventario y la selección de stories pueden contradecirse sobre la misma foto.

---

## 2. Alcance

### 2.1 IN
- `ingest/orientation.py`:
  - `AssetOrientation` (frozen): `raw` (de las dimensiones), `effective` (tras aplicar el
    EXIF) y la propiedad `rotated` (cierto cuando difieren).
  - `detect_orientation(size, exif_orientation) -> AssetOrientation`.
- **Decisión de la ambigüedad**: la orientación *efectiva* es la que consume el pipeline;
  la cruda se conserva para poder explicar la diferencia.
- Tests contra los CA + capa secundaria.

### 2.2 OUT
- Mostrar la orientación en un reporte → HU-018.
- Elegibilidad por formato de salida (9:16, 4:5) → HU-074/HU-059.
- Cambiar `core.Orientation` → **prohibido**: `core` es dominio puro sin EXIF (charter §6.4).
- Rotar píxeles → E3 (revelado).
- Persistir la orientación efectiva en el catálogo → HU-012 ya guarda las medidas crudas;
  añadirla es aditivo y lo hará el consumidor que lo necesite (ver A-3).

### 2.3 Casos límite
| # | Caso | Tratamiento | Fuente |
|---|---|---|---|
| 1 | Sin EXIF o sin `Orientation` | Efectiva = cruda | HU-004 (72 de 82 fotos reales no la declaran) |
| 2 | Cuadrada con EXIF que gira | Sigue cuadrada: intercambiar ejes iguales no cambia nada | derivado |

---

## 3. Componentes

| Componente | Cambio | Verificado |
|---|---|---|
| `ingest/orientation.py` | nuevo | ✅ no existe en `develop` (da9f88f) |
| `ingest/__init__.py` | re-export | ✅ leído |
| `tests/ingest/test_orientation.py` | nuevo | ✅ no existe |

### 3.1 Reutilizables
| Componente | ¿Reutilizar? | Justificación |
|---|---|---|
| `core.Orientation` (HU-157) | Sí, **sin tocarlo** | Ya clasifica V/H/cuadrada desde medidas; se reutiliza el enum y la regla |
| `exif.oriented_size` (HU-004) | Sí | Ya traduce medidas crudas a visibles; esta HU no reimplementa el intercambio de ejes |
| `ExifOrientation.swaps_axes` (HU-004) | Sí | La condición de giro ya está tipada |
| `ImageSize` (HU-011) | Sí | Entrada de la función |

**Nota:** las cuatro piezas existen; esta HU **compone**, no construye. Es la señal de que
las HUs anteriores dejaron la superficie correcta.

---

## 4. Modelo de datos
`AssetOrientation` en memoria. Sin persistencia (ver §2.2).

---

## 5. Reglas de negocio

| # | Regla | Fuente | Implicación |
|---|---|---|---|
| RN-1 | La orientación auditada por el cliente es la **visible** | Maestro §8.2 (anotada a ojo sobre la imagen) | La efectiva es la que consume el pipeline |
| RN-2 | "`core/` no importa OpenCV ni EXIF" | charter §6.4 · `python.md` | La composición vive en `ingest`, nunca en `core` |
| RN-3 | Determinismo | charter §6.1 | Función pura: mismas entradas ⇒ misma salida |
| RN-4 | Cobertura ≥80% módulo tocado | Pre-Flight | Evidencia al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | Con EXIF que gira, efectiva ≠ cruda y `rotated` es cierto | test |
| V-2 | Sin EXIF, efectiva = cruda y `rotated` es falso | test |
| V-3 | `core.Orientation` no cambia | los 17 tests de HU-157 siguen verdes |

---

## 6. Preguntas abiertas

### P-1 — ¿Se persiste la orientación efectiva en el catálogo?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** todavía no. El catálogo guarda las medidas crudas y la orientación
  se deriva; añadir un campo redundante invita a que se desincronicen. Cuando HU-018 defina
  el reporte, decidirá si lo necesita persistido o derivado al vuelo.
- **Costo si se asume mal:** campo aditivo en el esquema v1 (que ya tiene versión).
- **Estado:** ABIERTA (transferida a HU-018)

### P-2 — ¿Debe exponerse la discrepancia como flag del asset?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** se expone como propiedad (`rotated`), no como flag de calidad. Un
  flag sugiere problema, y una foto girada por EXIF es perfectamente normal — es lo que hace
  cualquier móvil al fotografiar en vertical.
- **Estado:** ABIERTA

---

## 7. Asunciones

| # | Asunción | Cubre | Costo si se rompe |
|---|---|---|---|
| A-1 | La efectiva es la que consume el pipeline; la cruda se conserva para explicar | — | Cambiar qué campo leen los consumidores |
| A-2 | Sin EXIF ⇒ efectiva = cruda | — | Ninguno |
| A-3 | No se persiste todavía | P-1 | Campo aditivo |

---

## 8. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| R-1 | Un consumidor lea `raw` creyendo que es la buena | media | medio | Nombres explícitos (`raw`/`effective`), docstring que lo dice, y `rotated` para detectar el caso |
| R-2 | Alguien intente meter EXIF en `core` para "simplificar" | baja | alto | El test de arquitectura ya prohíbe que `core` importe `ingest` |

---

## 9. Confianza global

- **Preguntas abiertas:** 2 — **0 bloqueantes**
- **Verificaciones cruzadas:**
  - [x] Codebase leído (`develop da9f88f`, 236 tests verdes)
  - [x] Consumidores cruzados en el backlog — **hallazgo: ninguno la declara como dependencia**
  - [x] Tensión heredada leída en la spec y el feedback de HU-004
  - [x] **Medición sobre el lote real**: V=76 · H=20 · cuadradas=4; solo 10 fotos declaran EXIF Orientation y todas con valor 1
  - [x] Reutilizables verificados en el código: las 4 piezas existen, esta HU compone
- **Recomendación:** ✅ **LISTA PARA DEV** (0 bloqueantes · ≥85%)
- **Confianza: 91%.** El 9%: R-1 (que un consumidor lea el campo equivocado) y P-1.

---

## 10. Dependencias
| ID | Relación | Estado |
|---|---|---|
| HU-157, HU-004, HU-011 | Aportan enum, EXIF y medidas | DONE |
| HU-018, HU-059, HU-074 | Consumidores | backlog |

---

## 11. Criterios de aceptación

- **CA-1** — Sin EXIF: efectiva = cruda, `rotated` falso.
- **CA-2** — Con `Orientation` 1, 2, 3 y 4 (no giran): efectiva = cruda.
- **CA-3** — Con `Orientation` 5, 6, 7 y 8 (giran): efectiva = la opuesta, `rotated` cierto.
- **CA-4** — Una foto cuadrada sigue cuadrada aunque el EXIF gire, y `rotated` es falso.
- **CA-5** — Función pura: dos llamadas con las mismas entradas dan el mismo resultado.
- **CA-6** — `core.Orientation` intacto: los tests de HU-157 pasan sin modificación.
- **CA-7** — El test de arquitectura sigue verde (`core` no importa `ingest`).
- **CA-8** — Cobertura ≥80% y batería completa verde.
- **CA-9** — Trazabilidad en el gate-log.

---

## 12. Historial de cambios
| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación; resuelve la ambigüedad que HU-004 delegó explícitamente | Claude (ejecutor) |
