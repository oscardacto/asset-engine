# Spec Técnica `HU-009` — `Archivos corruptos o truncados: cuarentena con causa, pipeline sigue`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 90% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** separar los archivos utilizables de los que no lo son, dejando
  constancia de **por qué** se apartó cada uno, sin que un archivo malo detenga el lote.
- **Para quién:** HU-180 (resumen de fallos del run), HU-018 (reporte de inventario),
  HU-017 (CLI `ingest`), HU-011 (sumará su causa al mismo mecanismo).
- **Módulo / dominio:** `media_optimizer.ingest`. Cobertura exigida ≥80%.
- **No obvio (lo crítico que el ticket no dice de frente):** "cuarentena" **no puede
  mover ni copiar archivos**. Mover tocaría el original, que el charter §6.3 declara
  intocable; copiar duplicaría gigabytes de video sin aportar nada. La cuarentena es un
  **registro** de rutas con su causa. Y el segundo hallazgo: se puede detectar
  truncamiento **sin decodificar**, comprobando el marcador de fin que cada formato exige
  (JPEG termina en `FFD9`, PNG en el chunk `IEND`, WebP declara su tamaño en la cabecera)
  — barato, y captura el caso real del archivo a medio descargar de WhatsApp.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- `ingest/quarantine.py`:
  - `QuarantineReason` (StrEnum): `UNREADABLE`, `EMPTY`, `UNKNOWN_FORMAT`,
    `UNSUPPORTED_FORMAT`, `TRUNCATED`.
  - `QuarantinedAsset` (frozen): `path`, `reason`, `detail` (texto accionable).
  - `TriageResult` (frozen): `accepted: tuple[Path, ...]` +
    `quarantined: tuple[QuarantinedAsset, ...]`.
  - `triage_media(paths) -> TriageResult` — clasifica sin interrumpirse ante un fallo.
- Detección de truncamiento por **marcador de cierre** propio de cada formato soportado.
- Orden determinista en ambas listas (independiente del orden de entrada).
- Tests contra los CA + capa secundaria etiquetada.

### 2.2 OUT — NO entra (delimitaciones)
- **Mover o copiar** archivos a una carpeta de cuarentena → prohibido por charter §6.3;
  el layout de salidas es HU-016.
- Escribir el registro a disco (JSON/Markdown) → HU-016/018 (con el ADR de catálogo HU-153).
- Límite de dimensiones / imágenes-bomba → **HU-011**, que añadirá su causa a este enum.
- Decodificar la imagen para validar integridad real → HU-011/020. Aquí la validación es
  estructural (firma + cierre), no semántica.
- Reintentos, resumen agregado del run y métricas por etapa → HU-168/180.
- Sidecar de etiquetas manuales para rescatar un descarte → HU-019.

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | Un archivo corrupto en medio del lote | El lote continúa; el archivo queda registrado con causa | ticket ("pipeline sigue") · `python.md` |
| 2 | Archivo truncado (descarga a medias) | Causa `TRUNCATED`, distinguible de "no es una imagen" | ticket ("corruptos **o truncados**") |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- ¿La cuarentena mueve archivos? → P-1 (resuelto por el charter, se documenta igual).
- ¿Qué pasa con formatos sin marcador de cierre verificable? → P-2.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `src/media_optimizer/ingest/quarantine.py` | nuevo | bajo | ✅ no existe en `develop` (a0a89a6) |
| `src/media_optimizer/ingest/__init__.py` | modif (re-export) | bajo | ✅ leído — exporta 9 nombres |
| `tests/ingest/test_quarantine.py` | nuevo | bajo | ✅ no existe |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| `detect_image_format` / `SUPPORTED_FORMATS` (HU-002) | Sí | Aportan tres de las cinco causas sin escribir lógica nueva |
| `core.CorruptMediaError` (HU-161) | Sí | Su `reason` se convierte directamente en el `detail` de la cuarentena |
| `truncated_jpeg` / `not_an_image` (HU-166) | Sí | Los fixtures de archivos rotos ya existen — fueron diseñados para esta HU |
| Patrón frozen dataclass + StrEnum de `core/` | Sí (estilo) | Consistencia del dominio |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| `QuarantinedAsset` / `TriageResult` (en memoria) | nuevos tipos | path, reason, detail / accepted, quarantined | N/A — persistencia en HU-016/018 |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "**No destructivo** — originales intactos" | charter §6.3 | No | La cuarentena registra, no mueve ni copia; solo lectura |
| RN-2 | "un archivo corrupto degrada ese asset, **nunca tumba el pipeline**" | `python.md` · ticket | No | `triage_media` captura por archivo y sigue: una ruta ilegible no aborta el recorrido |
| RN-3 | "cuarentena **con causa**" | ticket | No | Causa tipada (`QuarantineReason`) **más** detalle legible: la primera para agrupar en el resumen, el segundo para que el usuario entienda |
| RN-4 | "mensajes de error accionables, nunca stacktrace" | backlog HU-136 | No | El `detail` dice qué pasa y, cuando aplica, qué hacer (ej. HEIC ⇒ convertir a JPEG) |
| RN-5 | Determinismo sin dependencia del orden del filesystem | `python.md` · charter §6.1 | No | Ambas listas ordenadas por ruta; misma entrada ⇒ mismo resultado |
| RN-6 | Cero números mágicos | `python.md` | Parcial | Los marcadores de cierre son constantes de formato (como las firmas de HU-002), en tabla del módulo |
| RN-7 | Cobertura ≥80% módulo tocado | CLAUDE.md Pre-Flight | No | Evidencia `pytest --cov` al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | Un archivo apartado nunca aparece también en `accepted` | test lo garantiza (particiones disjuntas) |
| V-2 | La suma de ambas listas es exactamente la entrada | test lo garantiza (nada se pierde en silencio) |
| V-3 | Los archivos del disco quedan intactos tras el triaje | test lo garantiza |

---

## 6. Preguntas abiertas

### P-1 — ¿"Cuarentena" implica mover los archivos a una carpeta aparte?
- **Categoría:** INFORMATIVA (resuelta por la constitución, se documenta para que nadie la reabra)
- **Importa porque:** la palabra sugiere mover, y hacerlo violaría el principio más duro del proyecto.
- **Va dirigida a:** @oscardacto (ratificable con la integración).
- **Mi mejor hipótesis:** no — registro en memoria; si algún día se quiere una carpeta de
  descartes, sería de **enlaces o rutas**, nunca de los originales, y viviría en HU-016.
- **Si se asume mal, costo:** una función de exportación aditiva en HU-016.
- **Estado:** ABIERTA

### P-2 — ¿Formatos cuyo cierre no se puede verificar barato?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** los tres soportados sí se pueden (JPEG `FFD9`, PNG `IEND`, WebP
  por el tamaño declarado en la cabecera RIFF). Si un formato futuro no lo permitiera, la
  ausencia de comprobación es **fail-safe**: se acepta y la decodificación posterior lo
  detectará. Nunca se aparta por no poder comprobar.
- **Si se asume mal, costo:** ninguno — solo se pierde detección temprana.
- **Estado:** ABIERTA

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Cuarentena = registro en memoria, sin tocar el disco | P-1 | Exportación aditiva en HU-016 |
| A-2 | Truncamiento se comprueba por marcador de cierre; no comprobable ⇒ se acepta (fail-safe) | P-2 | Ninguno |
| A-3 | Un archivo vacío se reporta como `EMPTY`, no como "formato desconocido" — es más accionable | — | Cambio de una rama |
| A-4 | Validación estructural, no semántica: una imagen con cierre correcto pero píxeles corruptos se acepta aquí y la atrapa la decodificación | — | Ninguno (por diseño) |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | Falso positivo: un JPEG válido con bytes extra tras `FFD9` (algunos móviles añaden relleno) se marcaría truncado | datos | media | **alto** (descartar material bueno) | Buscar el marcador en la **cola** del archivo, no exigir que sean los dos últimos bytes exactos; test con relleno posterior |
| R-2 | Falso negativo: archivo truncado justo después del marcador de cierre de un chunk | datos | baja | bajo | Aceptable: la decodificación posterior lo atrapa (A-4) |
| R-3 | Coste de leer la cola de cada archivo | rendimiento | baja | bajo | Solo se leen los últimos bytes, con `seek` desde el final: no depende del tamaño del archivo |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (2 INFORMATIVAS)
- **Asunciones tomadas:** 4
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop a0a89a6`: `ingest/` con scanner/formats/hashing, 128 tests verdes)
  - [x] Causas ya disponibles verificadas en el código de HU-002 (None / no soportado / `CorruptMediaError`)
  - [x] Fixtures de archivos rotos verificados en HU-166 (`truncated_jpeg`, `not_an_image`)
  - [x] Conflicto "cuarentena vs no destructivo" cruzado contra charter §6.3 antes de diseñar
  - [x] Componentes reutilizables buscados (§3.1)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 90% — el 10%: R-1 (falso positivo de truncamiento, mitigado buscando el marcador en la cola) y P-1/P-2.

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-002 | Aporta la detección de formato (3 de 5 causas) | DONE |
| HU-161 | Aporta `CorruptMediaError` | DONE |
| HU-166 | Aporta los fixtures de archivos rotos | DONE |
| HU-011 | **Añadirá su causa** (imagen-bomba) a este enum | backlog |
| HU-016, HU-017, HU-018, HU-180 | Consumen el registro | backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna.

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — El lote continúa pese a un archivo malo
- **Given:** un lote con una foto válida, una ruta inexistente y basura binaria
- **When:** se ejecuta el triaje
- **Then:** la foto válida queda aceptada y las otras dos apartadas — sin excepción propagada

### CA-2 — Cada causa se distingue
- **Given:** un archivo ilegible, uno vacío, basura sin firma, un HEIC y un JPEG truncado
- **Then:** las causas son `UNREADABLE`, `EMPTY`, `UNKNOWN_FORMAT`, `UNSUPPORTED_FORMAT` y `TRUNCATED` respectivamente

### CA-3 — El detalle es accionable
- **Given:** un archivo HEIC
- **Then:** el `detail` menciona el formato concreto, no un mensaje genérico

### CA-4 — Truncado detectado sin decodificar
- **Given:** un JPEG cortado al 50% por el generador de fixtures
- **Then:** se aparta como `TRUNCATED`, y el mismo JPEG completo se acepta

### CA-5 — Sin falsos positivos por relleno
- **Given:** un JPEG válido con bytes extra añadidos después del marcador de cierre
- **Then:** se acepta (no se marca truncado)

### CA-6 — Particiones disjuntas y completas
- **Given:** un lote mixto de N archivos
- **Then:** `accepted` + `quarantined` suman exactamente N, sin intersección

### CA-7 — Determinismo
- **Given:** el mismo lote pasado en distinto orden
- **Then:** ambas listas salen idénticas

### CA-8 — No destructivo
- **Then:** bytes y `mtime` de todos los archivos quedan idénticos tras el triaje

### CA-9 — Cobertura del módulo ≥80%
- **Then:** `pytest --cov=media_optimizer.ingest` ≥ 80%

### CA-10 — Batería completa verde
- **Then:** pytest · ruff check + format --check · mypy, todo exit 0

### CA-11 — Trazabilidad
- **Then:** gate-log con `draft`, `gate_spec`, `dev` de HU-009

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial y evaluación de gate | Claude (ejecutor) |
