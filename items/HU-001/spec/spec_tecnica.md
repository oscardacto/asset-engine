# Spec Técnica `HU-001` — `Escaneo de carpeta de entrada con orden determinista e independiente del filesystem`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 89% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** recorrer la carpeta de entrada y devolver los archivos candidatos en un
  orden **estable y reproducible**, que no dependa de cómo el sistema de archivos los
  enumere ni del sistema operativo.
- **Para quién:** HU-002 (formatos por magic bytes), HU-006 (hash y duplicados),
  HU-010 (nombres hostiles), HU-017 (CLI `ingest`) — es la puerta de entrada del pipeline.
- **Módulo / dominio:** nuevo paquete `media_optimizer.ingest` — capa de infraestructura
  (toca el filesystem; **no** es `core/`). Cobertura exigida ≥80%.
- **No obvio (lo crítico que el ticket no dice de frente):** el escaneo devuelve **rutas,
  no `MediaAsset`s**. Un `MediaAsset` exige dimensiones y hash de contenido, que solo se
  conocen tras decodificar (HU-002) y hashear (HU-006); construirlo aquí obligaría a leer
  cada archivo dos veces. Y el determinismo no lo da "ordenar alfabéticamente" a secas:
  hay que fijar también la forma Unicode del nombre (la misma "ó" tiene dos
  representaciones válidas según el SO) y un desempate estable entre mayúsculas y
  minúsculas.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- Paquete `src/media_optimizer/ingest/` con `scanner.py`:
  - `scan_input_folder(root: Path, recursive: bool = True) -> tuple[Path, ...]`
- **Orden determinista** por clave compuesta sobre la ruta relativa en formato POSIX:
  `(NFC-casefold, NFC-exacto)` — primaria insensible a mayúsculas (orden legible para el
  reporte de inventario de HU-018), secundaria exacta (desempate estable donde el SO
  permite `A.jpg` y `a.jpg` coexistiendo).
- **Sin seguir enlaces simbólicos de directorio** (`Path.walk(follow_symlinks=False)`):
  evita ciclos infinitos ante una carpeta que se apunta a sí misma.
- Se omiten directorios y entradas ocultas (nombre que empieza por `.`): nunca son medios
  del usuario y contaminarían el lote.
- Validación de entrada con los errores del dominio (HU-161): ruta inexistente o que no
  es directorio ⇒ `InvalidInputError` con mensaje accionable.
- Tests contra los CA + capa secundaria etiquetada.

### 2.2 OUT — NO entra (delimitaciones)
- Filtrar por formato/extensión → **HU-002** (explícitamente "magic bytes, no extensión");
  el escaneo devuelve todos los archivos y HU-002 decide cuáles son medios válidos.
- Hash y duplicados → HU-006 · Normalización de nombres hostiles y colisiones → HU-010.
- Construir `MediaAsset` → ocurre cuando HU-002+HU-006 aporten dimensiones y hash.
- Metadatos de video → HU-014 · Persistencia del catálogo → HU-012.
- **Reportar subcarpetas ilegibles** en un resumen → pertenece a `StageReport` (HU-168) y
  al orquestador (HU-180); hoy el recorrido las omite y sigue (ver R-1 y P-3).

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | "independiente del filesystem" | El orden no puede heredar el de `scandir`, que varía entre SO y tras modificar la carpeta | ticket HU-001 |
| 2 | Carpeta vacía | Resultado vacío, sin error: es un lote legítimo de cero elementos | `python.md` (fail safe en datos del usuario) |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- Ubicación del módulo: `ingest/` no existe en la tabla de CLAUDE.md → P-1.
- Recursividad por defecto → P-2. · Subcarpetas ilegibles → P-3.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `src/media_optimizer/ingest/__init__.py` + `scanner.py` | nuevo paquete | bajo | ✅ no existe en `develop` (cf60453) |
| `tests/ingest/test_scanner.py` | nuevo | bajo | ✅ no existe |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| `core.InvalidInputError` (HU-161) | Sí | Primer consumidor real de la jerarquía de errores: ruta inválida es error de entrada del usuario, no bug |
| `media_optimizer.testing.write_jpeg` (HU-166) | Sí | Puebla carpetas de prueba con archivos reales decodificables, sin medios del cliente |
| `pathlib.Path.walk` (3.12+) | Sí | `follow_symlinks=False` por defecto y control de errores — evita el ciclo de symlinks sin código propio |
| `unicodedata.normalize` (stdlib) | Sí | Clave de orden estable entre SO; cero dependencias nuevas |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| N/A — devuelve rutas; no construye ni persiste contratos | read (solo listado de directorio) | — | N/A |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "orden determinista e **independiente del filesystem**" | ticket HU-001 | No | Orden impuesto por clave calculada sobre el nombre, nunca el de enumeración del SO |
| RN-2 | "misma entrada + mismo perfil ⇒ misma salida" | charter §6.1 | No | Dos escaneos de la misma carpeta devuelven la misma secuencia, en cualquier SO |
| RN-3 | "**No destructivo** — originales intactos" | charter §6.3 | No | Solo operaciones de lectura de directorio; jamás se abre, mueve ni modifica un archivo |
| RN-4 | "magic bytes, **no extensión**" | backlog HU-002 | No | El escaneo NO filtra por extensión — devolvería falsos negativos que HU-002 nunca vería |
| RN-5 | "entradas hostiles se validan antes de procesar" | `python.md` | No | Ruta inexistente/no-directorio ⇒ `InvalidInputError`; symlinks de directorio no se siguen |
| RN-6 | "`pathlib.Path`, nunca `os.path`" | `python.md` | No | `Path.walk`/`Path.iterdir` en toda la implementación |
| RN-7 | Cobertura ≥80% módulo tocado | CLAUDE.md Pre-Flight | No | Evidencia `pytest --cov` al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | `root` existe | `InvalidInputError`: "la carpeta de entrada no existe: <ruta>" |
| V-2 | `root` es directorio | `InvalidInputError`: "la ruta de entrada no es una carpeta: <ruta>" |
| V-3 | El resultado no contiene directorios ni entradas ocultas | test lo garantiza |

---

## 6. Preguntas abiertas

### P-1 — ¿La ingesta vive en un módulo `ingest/` propio? (la tabla de módulos de CLAUDE.md no la contempla)
- **Categoría:** IMPORTANTE (no bloqueante: hay hipótesis fuerte y el costo de mover un módulo hoy es mínimo)
- **Importa porque:** E1 son 19 HUs y ninguna tiene hoy un módulo asignado en la
  constitución; la tabla lista `core/ vision/ photo/ video/ ranking/ profiles/ pipeline/
  cli/ config/` — ninguno encaja: `pipeline/` es orquestación de etapas, no lectura de
  disco, y `photo/` es análisis y revelado.
- **Va dirigida a:** @oscardacto (ratificable con el merge del PR).
- **Mi mejor hipótesis:** sí, `ingest/` — una épica completa con catálogo, validación y
  cuarentena merece su módulo; meterla en `pipeline/` mezclaría responsabilidades que la
  propia constitución separa. **Si se acepta, CLAUDE.md debería sumar esa fila** (cambio
  de gobernanza, decide el equipo — no lo hago unilateralmente).
- **Si se asume mal, costo:** mover un paquete de 2 archivos y ajustar imports.
- **Estado:** ABIERTA

### P-2 — ¿El escaneo es recursivo por defecto?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** sí (`recursive=True`) — las exportaciones de celular llegan en
  subcarpetas (DCIM, por fecha) y el cliente 0 organiza por series; escanear solo el nivel
  superior perdería material silenciosamente, que es el peor modo de fallar. El flag
  permite el caso "solo esta sesión".
- **Si se asume mal, costo:** cambiar un default.
- **Estado:** ABIERTA

### P-3 — ¿Qué se hace con una subcarpeta ilegible (permisos)?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** omitirla y continuar (coherente con "un asset que falla degrada,
  el lote continúa"). Reportarla en un resumen requiere `StageReport` (HU-168) y el
  orquestador (HU-180), que aún no existen; adelantar aquí una estructura de reporte sería
  inventar un contrato sin consumidor.
- **Si se asume mal, costo:** cambiar el tipo de retorno más adelante (afecta a HU-002/006).
- **Estado:** ABIERTA (transferida como nota de dependencia a HU-168/180)

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Módulo `ingest/` propio | P-1 | Mover paquete + ajustar imports |
| A-2 | `recursive=True` por defecto | P-2 | Cambiar default |
| A-3 | Subcarpetas ilegibles se omiten sin reportar (hoy) | P-3 | Cambio de firma en HU-168/180 |
| A-4 | Se omiten entradas ocultas (`.`) — nunca son medios del usuario | — | Añadir flag `include_hidden` (aditivo) |
| A-5 | Retorno `tuple[Path, ...]` (inmutable, consistente con el estilo de `core/`) | — | Cambio de tipo (mecánico) |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | Material perdido en silencio por subcarpeta ilegible | datos | baja | medio | A-3 documentada + nota transferida a HU-168/180 para el resumen de fallos |
| R-2 | Orden inestable entre Windows y Linux por formas Unicode distintas del mismo nombre | datos/determinismo | media | medio | Clave de orden normalizada a NFC antes de comparar; test con nombre acentuado |
| R-3 | Escaneo de un árbol enorme cargado entero en memoria | rendimiento | baja | bajo | Son rutas, no medios; un lote real del cliente 0 son decenas de archivos. Si algún día escala, la mitigación es un iterador — anotado para HU-165 |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 3 total — **0 bloqueantes** (1 IMPORTANTE, 2 INFORMATIVAS)
- **Asunciones tomadas:** 5
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop cf60453`: `core/` con 4 módulos, `testing/`, 77 tests verdes)
  - [x] Consumidores cruzados en el backlog (HU-002/003/006/010/017 — insumo §2)
  - [x] Tabla de módulos de CLAUDE.md verificada — **no contempla la ingesta** (origen de P-1)
  - [x] Componentes reutilizables buscados, no asumidos (§3.1: `InvalidInputError`, `write_jpeg`, `Path.walk`)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 89% — el 11%: P-1 (ubicación del módulo, con implicación de gobernanza) y R-1/P-3 (silencio ante subcarpetas ilegibles).

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-157 | Dependencia declarada en el backlog (contrato del dominio) | DONE |
| HU-161 | Aporta `InvalidInputError` | DONE |
| HU-166 | Aporta los fixtures para poblar carpetas de prueba | DONE |
| HU-002, HU-006, HU-010, HU-017 | Consumen esta lista | backlog |
| HU-168, HU-180 | Heredan la pregunta del reporte de subcarpetas ilegibles (P-3) | backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna.

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — Orden determinista e independiente del filesystem
- **Given:** una carpeta cuyos archivos se crearon en orden `c.jpg`, `a.jpg`, `b.jpg`
- **When:** se escanea dos veces
- **Then:** ambas ejecuciones devuelven la misma secuencia, ordenada por ruta (`a`, `b`, `c`) — no por orden de creación ni de enumeración del SO

### CA-2 — Recorrido recursivo con rutas completas
- **Given:** `raiz/foto1.jpg` y `raiz/sesion/foto2.jpg`
- **When:** se escanea con `recursive=True` (default)
- **Then:** aparecen ambos; con `recursive=False`, solo `foto1.jpg`

### CA-3 — Sin filtrar por extensión
- **Given:** una carpeta con `foto.jpg`, `documento.txt` y `sin_extension`
- **Then:** los tres aparecen — decidir qué es un medio válido es de HU-002

### CA-4 — Se omiten directorios y ocultos
- **Given:** una carpeta con un subdirectorio, un `.oculto.jpg` y una carpeta `.cache/` con archivos dentro
- **Then:** el resultado contiene solo archivos visibles; ni el directorio, ni el oculto, ni el contenido de `.cache/`

### CA-5 — Carpeta vacía es un lote legítimo
- **Then:** resultado vacío, sin excepción

### CA-6 — Entradas inválidas con error accionable
- **Given:** una ruta inexistente, y una ruta que apunta a un archivo
- **Then:** `InvalidInputError` en ambos casos, con un mensaje que nombra la ruta y el problema

### CA-7 — Estabilidad Unicode y mayúsculas
- **Given:** nombres con acentos (`camión.jpg`) y variantes de caja (`Foto.jpg`, `foto.jpg`)
- **Then:** el orden es el mismo sin importar la forma Unicode con que el SO devuelva el nombre, y las variantes de caja quedan juntas en orden estable

### CA-8 — No destructivo
- **Given:** una carpeta con archivos
- **When:** se escanea
- **Then:** los bytes y las marcas de tiempo de modificación de los archivos quedan idénticos

### CA-9 — Cobertura del módulo ≥80%
- **Then:** `pytest --cov=media_optimizer.ingest` ≥ 80%

### CA-10 — Batería completa verde
- **Then:** pytest · ruff check + format --check · mypy, todo exit 0

### CA-11 — Trazabilidad
- **Then:** gate-log con `draft`, `gate_spec`, `dev` de HU-001

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial y evaluación de gate | Claude (ejecutor) |
| 2026-07-26 | DEV: implementado según §2.1 con un refinamiento — la clave de orden pasó de 2 a 3 componentes (se añadió la ruta cruda como último desempate: dos nombres distintos pueden normalizar al mismo NFC y el orden entre ellos habría dependido del filesystem). Asunciones A-1…A-5 aplicadas; batería 92 tests verde, ingest/ 100% | Claude (ejecutor) |
