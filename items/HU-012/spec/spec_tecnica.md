# Spec Técnica `HU-012` — `Persistencia del catálogo (según ADR HU-153) con escritura atómica`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 88% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** guardar y recuperar el catálogo de un lote sin que sea posible
  corromperlo, en el formato que ya decidió ADR-003.
- **Para quién:** HU-013 (re-ingesta idempotente), HU-016 (directorio de trabajo),
  HU-017 (CLI `ingest`), HU-018 (reporte), HU-019 (etiquetas manuales), HU-035 (reportes
  de calidad), HU-182 (reanudación).
- **Módulo / dominio:** `media_optimizer.ingest` — módulo nuevo `catalog.py`. Cobertura ≥80%.
- **No obvio (lo crítico que el ticket no dice de frente):** el formato ya está decidido,
  así que lo que esta HU realmente resuelve son dos cosas distintas. **(1) El esquema debe
  poder crecer**: HU-035 añadirá reportes de calidad, HU-019 etiquetas manuales, HU-057
  historial — un catálogo escrito hoy tiene que seguir leyéndose mañana, así que necesita
  **versión declarada** desde la primera línea. **(2) Al leer, el catálogo es entrada
  hostil**: puede venir editado a mano, truncado por un corte de luz o de otra versión del
  programa; tratarlo como dato de confianza sería el mismo error que confiar en la
  extensión de un archivo.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- `ingest/catalog.py`:
  - `CATALOG_VERSION: int` y `CATALOG_FILENAME: str`.
  - `CatalogEntry` (frozen): un asset aceptado — `content_hash`, `source` (relativa a la
    raíz del lote), `media_type`, `width`, `height`, `orientation`.
  - `Catalog` (frozen): `version`, `root`, `entries: tuple[CatalogEntry, ...]`,
    `quarantined: tuple[QuarantineRecord, ...]`.
  - `QuarantineRecord` (frozen): `source`, `reason`, `detail` — versión serializable de
    `QuarantinedAsset`.
  - `save_catalog(catalog, directory) -> Path` — **escritura atómica** (temporal + `rename`).
  - `load_catalog(directory) -> Catalog` — valida y lanza `InvalidInputError` con mensaje
    accionable ante catálogo ilegible, mal formado o de versión desconocida.
- Serialización determinista: `sort_keys=True`, `ensure_ascii=False`, UTF-8, saltos `\n`,
  entradas ordenadas por ruta antes de escribir.
- **Rutas relativas a la raíz del lote**: un catálogo movido de carpeta o de máquina sigue
  siendo válido, y el archivo es idéntico venga de donde venga la raíz absoluta.
- Tests contra los CA + capa secundaria etiquetada.

### 2.2 OUT — NO entra (delimitaciones)
- Decidir si un asset ya estaba procesado / no reprocesar → **HU-013**.
- Layout del directorio de trabajo (dónde vive el catálogo) → HU-016.
- CLI y resumen en consola → HU-017 · Reporte legible → HU-018.
- Etiquetas manuales → HU-019 · `QualityReport` en el catálogo → HU-035 · Historial de
  transformaciones → HU-057. **Todas añaden secciones nuevas al esquema**: por eso hay
  versión.
- Migración entre versiones de esquema → cuando exista una segunda versión; hoy solo se
  detecta y se rechaza con mensaje claro.

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | Escritura interrumpida a mitad | El catálogo previo sobrevive intacto; nunca queda un archivo a medias | ADR-003 ("escritura atómica obligatoria, no opcional") |
| 2 | Lote vacío | Catálogo válido con cero entradas | charter (un lote de cero es legítimo) |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- ¿Rutas relativas o absolutas? → P-1. · ¿Qué hacer ante versión desconocida? → P-2.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `src/media_optimizer/ingest/catalog.py` | nuevo | medio (formato persistido: los errores se arrastran) | ✅ no existe en `develop` (f13f6eb) |
| `src/media_optimizer/ingest/__init__.py` | modif (re-export) | bajo | ✅ leído — 23 nombres |
| `tests/ingest/test_catalog.py` | nuevo | bajo | ✅ no existe |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| `core.MediaAsset` / `MediaType` / `Orientation` (HU-157) | Sí | El catálogo persiste exactamente lo que el contrato ya define; `CatalogEntry` es su forma serializable |
| `core.InvalidInputError` (HU-161) | Sí | Un catálogo corrupto es entrada inválida del usuario, con mensaje accionable |
| `QuarantinedAsset` / `QuarantineReason` (HU-009/011) | Sí | Sus 6 causas se persisten tal cual; el enum ya serializa a texto plano |
| `json` (stdlib) | Sí | ADR-003; cero dependencias nuevas |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| Manifiesto `catalog.json` | crear/leer | version, root, entries[], quarantined[] | N/A — esta HU **define** el esquema |
| `MediaAsset` | origen de los campos de `entries` | media_type, width, height, content_hash, source | ✅ verificado en el código |
| `QuarantinedAsset` | origen de `quarantined` | path, reason, detail | ✅ verificado en el código |

### 4.2 Migraciones/cambios de esquema requeridos
- [x] Sí — **este WorkItem crea el esquema v1**. No hay datos previos que migrar.
- [ ] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "**escritura atómica obligatoria (temporal + `rename`)** — requisito de HU-012, no opcional" | ADR-003 | No | Nunca se escribe sobre el archivo final; se escribe al lado y se renombra |
| RN-2 | "`sort_keys=True`, `ensure_ascii=False`, UTF-8, indentado estable" · "las colecciones se ordenan por una clave explícita del dominio" | ADR-003 | No | Serializador con esos parámetros fijos; entradas ordenadas por ruta |
| RN-3 | "misma entrada ⇒ misma salida byte a byte" | charter §6.1 | No | Dos guardados del mismo contenido producen archivos idénticos, sin importar el orden de llegada |
| RN-4 | "Re-ingesta idempotente" (HU-013) y "sobrevive re-ingestas" (HU-019) | backlog | No | El esquema lleva **versión** y el hash como identidad estable del asset |
| RN-5 | "Entradas hostiles se validan antes de procesar" | `python.md` | No | El catálogo leído se valida campo a campo antes de construir los contratos |
| RN-6 | "No destructivo — toda salida a directorio de trabajo" | charter §6.3 | No | El catálogo se escribe en el directorio que se le indique, jamás junto a los originales por defecto |
| RN-7 | Cobertura ≥80% módulo tocado | CLAUDE.md Pre-Flight | No | Evidencia `pytest --cov` al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | El archivo es JSON válido | `InvalidInputError`: "el catálogo no es un JSON válido: <ruta>" |
| V-2 | `version` presente y conocida | `InvalidInputError` nombrando la versión encontrada y la soportada |
| V-3 | Cada entrada tiene los campos obligatorios y tipos correctos | `InvalidInputError` nombrando la entrada problemática |
| V-4 | Guardar y volver a cargar devuelve un catálogo equivalente | test de ida y vuelta lo garantiza |

---

## 6. Preguntas abiertas

### P-1 — ¿Las rutas del catálogo son relativas o absolutas?
- **Categoría:** INFORMATIVA
- **Importa porque:** decide si el catálogo sobrevive a mover la carpeta o a compartirla.
- **Mi mejor hipótesis:** **relativas a la raíz del lote**, que se guarda una sola vez en
  el campo `root`. Rutas absolutas incrustarían `C:\Users\usuario\…` en cada entrada,
  romperían el determinismo entre máquinas y filtrarían el nombre de usuario a un archivo
  que puede compartirse.
- **Si se asume mal, costo:** re-generar catálogos (hoy no existe ninguno).
- **Estado:** ABIERTA

### P-2 — ¿Qué se hace ante un catálogo de versión desconocida?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** rechazar con mensaje accionable que nombre ambas versiones, no
  intentar leerlo "a ver si funciona". Un catálogo de versión futura leído a medias
  produciría datos silenciosamente incompletos, que es peor que un error claro.
- **Si se asume mal, costo:** añadir una capa de migración cuando exista la v2.
- **Estado:** ABIERTA

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Rutas relativas a `root`, guardado una vez | P-1 | Re-generar catálogos |
| A-2 | Versión desconocida ⇒ error claro, sin intento de lectura parcial | P-2 | Capa de migración futura |
| A-3 | `CATALOG_VERSION = 1`; el nombre del archivo es `catalog.json` | — | Constante |
| A-4 | El catálogo persiste **entradas aceptadas y apartadas**, porque HU-018 debe reportar ambas y HU-013 no debe reintentar lo ya descartado | — | Sección adicional |
| A-5 | La orientación persistida es la derivada de las dimensiones almacenadas (`core.Orientation`), no la efectiva post-EXIF — **esa distinción la resuelve HU-005** | — | Campo adicional cuando HU-005 decida |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | Un esquema mal diseñado se arrastra: hay 7 HUs que van a construir encima | técnico | media | **alto** | Versión desde v1 + secciones separadas (`entries` / `quarantined`) para que añadir una nueva no toque las existentes |
| R-2 | `rename` no atómico en el sistema de archivos de destino | técnico | baja | alto | `Path.replace` es atómico en el mismo volumen en Windows y POSIX; el temporal se crea **en el mismo directorio** para garantizarlo (si se creara en `/tmp` sería un `move` entre volúmenes, no atómico) |
| R-3 | Rutas absolutas filtrando el nombre de usuario a un archivo compartible | seguridad/PII | media | medio | A-1: rutas relativas |
| R-4 | Catálogo enorme cargado entero en memoria | rendimiento | baja | bajo | Consecuencia aceptada de ADR-003, con disparadores de reconsideración ya escritos allí |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (2 INFORMATIVAS)
- **Asunciones tomadas:** 5
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop f13f6eb`: `ingest/` con 6 módulos, 193 tests verdes)
  - [x] Contratos de origen verificados en el código (`MediaAsset`, `QuarantinedAsset`, enums que ya serializan a texto plano)
  - [x] **Los 7 consumidores cruzados en el backlog** con su fila literal (insumo §2) — de ahí sale la necesidad de versión y de secciones separables
  - [x] Decisión de formato ya cerrada y leída (ADR-003 Aceptado), no re-litigada
  - [x] Componentes reutilizables buscados (§3.1 — cero dependencias nuevas)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 88% — el 11-12%: R-1 (es el artefacto con más consumidores futuros de todo lo construido hasta ahora) y A-5 (la orientación efectiva depende de una decisión de HU-005 aún no tomada).

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-153 (ADR-003) | Decide el formato | DONE / Aceptado |
| HU-157, HU-161, HU-009, HU-011 | Aportan contratos, errores y causas de cuarentena | DONE |
| HU-013, HU-016, HU-017, HU-018, HU-019, HU-035, HU-182 | Construyen sobre este esquema | backlog |
| HU-005 | Decidirá si la orientación persistida cambia (A-5) | backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna.

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — Ida y vuelta fiel
- **Given:** un catálogo con entradas aceptadas y apartadas
- **When:** se guarda y se vuelve a cargar
- **Then:** el catálogo cargado es igual al original

### CA-2 — Escritura atómica: el catálogo previo sobrevive
- **Given:** un catálogo ya guardado y un fallo a mitad de la escritura del siguiente
- **When:** el guardado falla
- **Then:** el archivo en disco sigue siendo el catálogo anterior, íntegro y cargable — y no queda ningún archivo temporal suelto

### CA-3 — Determinismo byte a byte
- **Given:** el mismo contenido lógico con las entradas en distinto orden
- **When:** se guarda dos veces
- **Then:** los bytes del archivo son idénticos

### CA-4 — Rutas relativas
- **Given:** un lote en una raíz cualquiera
- **Then:** el archivo no contiene la ruta absoluta de la raíz en cada entrada, y el catálogo sigue siendo cargable si la carpeta se mueve

### CA-5 — Catálogo corrupto degrada con mensaje accionable
- **Given:** un archivo que no es JSON, uno con un campo obligatorio ausente y uno con un tipo incorrecto
- **Then:** `InvalidInputError` en los tres casos, con un mensaje que nombre el problema concreto

### CA-6 — Versión desconocida se rechaza
- **Given:** un catálogo con `version` mayor que la soportada
- **Then:** `InvalidInputError` nombrando la versión encontrada y la soportada

### CA-7 — Lote vacío es válido
- **Then:** un catálogo sin entradas se guarda y se carga sin error

### CA-8 — No destructivo
- **Given:** una carpeta de originales
- **Then:** guardar el catálogo en el directorio de trabajo no altera ningún archivo de origen

### CA-9 — Cobertura del módulo ≥80%
- **Then:** `pytest --cov=media_optimizer.ingest` ≥ 80%

### CA-10 — Batería completa verde
- **Then:** pytest · ruff check + format --check · mypy, todo exit 0

### CA-11 — Trazabilidad
- **Then:** gate-log con `draft`, `gate_spec`, `dev` de HU-012

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial y evaluación de gate | Claude (ejecutor) |
