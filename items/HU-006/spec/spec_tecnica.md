# Spec Técnica `HU-006` — `Hash de contenido y detección de duplicados exactos`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 93% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** una huella estable del contenido de cada archivo, y el agrupamiento de
  los que comparten exactamente la misma.
- **Para quién:** `MediaAsset.content_hash` (identidad del asset en todo el pipeline),
  HU-012/013 (catálogo y re-ingesta idempotente), HU-018 (reporte de inventario).
- **Módulo / dominio:** `media_optimizer.ingest`. Cobertura exigida ≥80%.
- **No obvio (lo crítico que el ticket no dice de frente):** la optimización clásica de
  "agrupar por tamaño y hashear solo los que coinciden" **aquí no sirve**: todo asset
  necesita su hash igualmente para el catálogo, así que el pre-filtro no ahorraría ni una
  lectura. Y el hash debe leerse **por bloques**: un video de 2 GB no puede entrar a RAM
  (`python.md`), y ese requisito aplica desde ya aunque hoy solo haya fotos.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- `ingest/hashing.py`:
  - `HASH_ALGORITHM: str` = `"sha256"` (nombre publicable junto al hash en el catálogo).
  - `compute_content_hash(path) -> str` — SHA-256 en hexadecimal minúscula, leído en
    bloques de 1 MiB.
  - `DuplicateGroup` (frozen): `content_hash: str` + `paths: tuple[Path, ...]`.
  - `find_duplicate_groups(paths) -> tuple[DuplicateGroup, ...]` — solo grupos de 2 o más,
    con orden determinista dentro del grupo y entre grupos.
- Archivo ilegible ⇒ `CorruptMediaError(source, reason)`, igual que en HU-002 (coherencia
  de la capa de ingesta).
- Tests contra los CA + capa secundaria etiquetada, incluido un **vector conocido** de
  SHA-256 que prueba que se computa el algoritmo estándar y no una variante propia.

### 2.2 OUT — NO entra (delimitaciones)
- Qué hacer con los duplicados (cuál conservar, descartar o solo marcar) → HU-012/013/018.
- **Near-duplicates** perceptuales (misma escena, distinta compresión) → HU-075, es otra
  técnica (hash perceptual), no una variante de esta.
- Persistencia del hash en el catálogo → HU-012 (tras el ADR de catálogo, HU-153).
- Construir `MediaAsset` → necesita además las dimensiones (decodificación, HU-011/020).
- Hash de fotogramas o de contenido de video → E5.

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | Copias de WhatsApp con nombres distintos (`… (1).jpg`) | Mismo hash ⇒ mismo grupo: el nombre no participa | Maestro §8.1 (archivo degradado por WhatsApp) |
| 2 | Sin duplicados en el lote | Resultado vacío, no un grupo por archivo | ticket ("duplicados", no "índice de hashes") |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- ¿Elección de algoritmo? → P-1. · ¿EXIF distinto con píxeles iguales? → P-2.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `src/media_optimizer/ingest/hashing.py` | nuevo | bajo | ✅ no existe en `develop` (2d9c319) |
| `src/media_optimizer/ingest/__init__.py` | modif (re-export) | bajo | ✅ leído — exporta 5 nombres |
| `tests/ingest/test_hashing.py` | nuevo | bajo | ✅ no existe |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| `core.CorruptMediaError` (HU-161) | Sí | Mismo tratamiento que en HU-002: ilegible ⇒ degrada con causa |
| `media_optimizer.testing` (HU-166) | Sí | `encode_jpeg`/`flat_image` dan bytes reales y **deterministas** — imprescindible para probar que dos copias hashean igual |
| `hashlib` (stdlib) | Sí | Cero dependencias nuevas |
| Patrón de dataclass frozen de `core/` | Sí (estilo) | `DuplicateGroup` sigue la convención del dominio |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| `DuplicateGroup` (en memoria) | nuevo tipo de retorno | content_hash, paths | N/A |
| `MediaAsset.content_hash` | consumidor futuro | — | ✅ verificado: el contrato lo declara `str` opaco no vacío (HU-157) |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "**nunca cargar el video completo a RAM**" | `python.md` | No | Lectura por bloques de 1 MiB; el pico de memoria no depende del tamaño del archivo |
| RN-2 | "Determinismo […] sin dependencia del orden del filesystem" | `python.md` · charter §6.1 | No | Mismo contenido ⇒ mismo hash siempre; grupos y miembros ordenados por ruta, no por orden de llegada |
| RN-3 | "Re-ingesta idempotente: mismo input no duplica ni reprocesa" | backlog HU-013 | No | El hash es la clave de identidad estable: debe depender **solo** del contenido, nunca del nombre, la ruta ni la fecha |
| RN-4 | "un archivo corrupto degrada ese asset, nunca tumba el pipeline" | `python.md` | No | `CorruptMediaError` con causa; el llamador decide |
| RN-5 | "No destructivo — originales intactos" | charter §6.3 | No | Solo lectura binaria |
| RN-6 | Prohibido `md5`/`sha1` (checklist de seguridad) | `python.md` | No | SHA-256 pasa la regla `S324` de ruff sin excepciones |
| RN-7 | Cobertura ≥80% módulo tocado | CLAUDE.md Pre-Flight | No | Evidencia `pytest --cov` al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | El archivo se puede abrir y leer completo | `CorruptMediaError` nombrando ruta y causa |
| V-2 | Dos archivos con el mismo contenido y distinto nombre caen en el mismo grupo | test lo garantiza |
| V-3 | El hash coincide con el SHA-256 estándar (vector conocido) | test lo garantiza |

---

## 6. Preguntas abiertas

### P-1 — ¿SHA-256 o BLAKE2b?
- **Categoría:** INFORMATIVA
- **Importa porque:** el hash quedará escrito en el catálogo de todos los lotes; cambiarlo
  después invalida los catálogos existentes.
- **Va dirigida a:** @oscardacto (ratificable en el PR).
- **Mi mejor hipótesis:** SHA-256 — es **verificable a mano** con `Get-FileHash` o
  `sha256sum`, algo que importa en una herramienta local y auditable donde el usuario debe
  poder comprobar el catálogo sin ejecutar nuestro código. BLAKE2b sería más rápido en CPU,
  pero el hashing aquí está limitado por la lectura de disco, no por el cálculo.
- **Si se asume mal, costo:** re-hashear catálogos existentes (hoy: ninguno).
- **Estado:** ABIERTA

### P-2 — Dos fotos con los mismos píxeles pero EXIF distinto, ¿son duplicados?
- **Categoría:** INFORMATIVA
- **Importa porque:** define qué significa "exacto" en el ticket.
- **Mi mejor hipótesis:** no son duplicados aquí — el hash cubre **todos los bytes** del
  archivo, así que un EXIF distinto da un hash distinto. Es lo correcto para el uso de
  identidad (dos archivos distintos son dos assets distintos), y detectar "misma imagen,
  distinto metadato" es justo el trabajo de HU-075 (near-duplicates).
- **Si se asume mal, costo:** ninguno en este módulo; sería una función adicional en HU-075.
- **Estado:** ABIERTA (nota de dependencia para HU-075)

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | SHA-256, hex en minúscula, sin prefijo de algoritmo (comparable directo con herramientas del SO) | P-1 | Re-hashear catálogos |
| A-2 | "Duplicado exacto" = archivo byte a byte idéntico | P-2 | Función adicional en HU-075 |
| A-3 | Bloque de 1 MiB — constante de rendimiento del módulo; promovible a `config/` en HU-155 si alguna vez se afina | — | Mover una constante |
| A-4 | Un archivo vacío es hasheable (SHA-256 del vacío) y dos vacíos son duplicados entre sí | — | Filtrado previo en HU-009 |
| A-5 | Sin pre-filtro por tamaño: todo asset necesita su hash igualmente (ver §1) | — | Optimización aditiva si el perfilado la justifica |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | Coste de hashear lotes grandes (archivo completo del cliente 0 + videos) | rendimiento | media | bajo | Limitado por IO, no por CPU; el presupuesto por etapa lo fija HU-165 (benchmarks). Anotado allí |
| R-2 | Confundir "duplicado exacto" con "misma foto" y creer que HU-075 ya está cubierta | proceso | media | medio | Delimitación explícita en §2.2 y en el docstring del módulo |
| R-3 | Un archivo modificado mientras se hashea produce una huella de un estado intermedio | datos | baja | bajo | Fuera de control del proceso (el usuario no debería tocar el origen durante el run); el charter ya declara los originales como read-only |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (2 INFORMATIVAS)
- **Asunciones tomadas:** 5
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop 2d9c319`: `ingest/` con scanner y formats, 113 tests verdes)
  - [x] Contrato `MediaAsset.content_hash` verificado en el código (str opaco no vacío — compatible con hex plano)
  - [x] Consumidores cruzados en el backlog (HU-012/013/018/075 — insumo §2)
  - [x] Regla de seguridad de hashes verificada en `python.md` (md5/sha1 prohibidos; SHA-256 cumple)
  - [x] Componentes reutilizables buscados (§3.1)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 93% — el 7%: P-1 (algoritmo, con coste de cambio bajo mientras no haya catálogos) y R-1 (rendimiento en lotes grandes, medible en HU-165).

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-001 | Entrega las rutas a hashear | DONE |
| HU-161 | Aporta `CorruptMediaError` | DONE |
| HU-166 | Aporta fixtures deterministas (dos copias idénticas reproducibles) | DONE |
| HU-157 | Consumidor del hash (`MediaAsset.content_hash`) | DONE |
| HU-012, HU-013, HU-018, HU-075 | Consumen hash y grupos | backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna.

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — El hash depende solo del contenido
- **Given:** el mismo contenido guardado como `a.jpg` y como `copia_de_a.jpg` en otra subcarpeta
- **Then:** ambos producen el mismo hash; un contenido distinto produce otro

### CA-2 — Es SHA-256 de verdad
- **Given:** un archivo vacío
- **Then:** el hash es `e3b0c442…b855`, el vector conocido de SHA-256 del contenido vacío

### CA-3 — Duplicados agrupados por contenido, no por nombre
- **Given:** `original.jpg`, `IMG (1).jpg` (copia idéntica) y `otra.jpg` (distinta)
- **Then:** un solo grupo, con las dos copias y su hash; `otra.jpg` no aparece

### CA-4 — Lote sin duplicados
- **Given:** tres archivos de contenido distinto
- **Then:** resultado vacío

### CA-5 — Orden determinista
- **Given:** dos grupos de duplicados, pasados en distinto orden de entrada
- **Then:** los grupos y sus rutas salen en el mismo orden en ambas llamadas

### CA-6 — Lectura por bloques
- **Given:** un archivo mayor que el bloque de lectura
- **Then:** el hash coincide con el de `hashlib` sobre el contenido completo (la partición no altera el resultado)

### CA-7 — Ilegible degrada con causa
- **Given:** una ruta inexistente
- **Then:** `CorruptMediaError` con `source` y causa en el mensaje

### CA-8 — No destructivo
- **Then:** bytes y `mtime` del archivo quedan idénticos tras hashear

### CA-9 — Cobertura del módulo ≥80%
- **Then:** `pytest --cov=media_optimizer.ingest` ≥ 80%

### CA-10 — Batería completa verde
- **Then:** pytest · ruff check + format --check · mypy, todo exit 0

### CA-11 — Trazabilidad
- **Then:** gate-log con `draft`, `gate_spec`, `dev` de HU-006

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial y evaluación de gate | Claude (ejecutor) |
