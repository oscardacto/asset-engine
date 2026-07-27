# Spec Técnica `HU-002` — `Validación de formatos de imagen soportados (magic bytes, no extensión)`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 92% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** clasificar cada archivo por su **firma binaria**, no por la extensión
  del nombre, y decidir si el pipeline sabe procesarlo.
- **Para quién:** HU-004 (EXIF), HU-007 (compresión WhatsApp), HU-009 (cuarentena con
  causa), HU-011 (imágenes-bomba), HU-017 (CLI `ingest`).
- **Módulo / dominio:** `media_optimizer.ingest` (ya existe, ratificado en HU-001).
  Cobertura exigida ≥80%.
- **No obvio (lo crítico que el ticket no dice de frente):** "no soportado" no es una sola
  categoría. Verificado empíricamente contra nuestro OpenCV lockeado: decodifica
  JPEG/PNG/WebP/TIFF pero **AVIF: NO** y **HEIC: ausente del build**. HEIC es el formato
  nativo de iPhone, así que llegará: si se responde "esto no es una imagen", el usuario no
  sabrá qué hacer; si se responde "es HEIC, conviértelo a JPEG", sí. Por eso el detector
  distingue **reconocido-y-soportado**, **reconocido-pero-no-soportado** y **desconocido**.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- `ingest/formats.py`:
  - `ImageFormat` (StrEnum): `JPEG`, `PNG`, `WEBP`, `HEIC`, `AVIF`.
  - `SUPPORTED_FORMATS: frozenset[ImageFormat]` = {JPEG, PNG, WEBP} (verificado contra
    el build real, no asumido).
  - `detect_image_format(path) -> ImageFormat | None` — `None` = firma desconocida.
  - `is_supported_image(path) -> bool`.
- Detección leyendo **solo los primeros 16 bytes** — deja intacta la puerta para el
  rechazo previo a decodificar de HU-011 (imágenes-bomba) y evita cargar archivos enormes.
- Familias de firma cubiertas: prefijo simple (JPEG, PNG), contenedor RIFF (WebP: `RIFF`
  en 0 + `WEBP` en 8) y contenedor ISO-BMFF (`ftyp` en 4 + marca en 8 → HEIC/AVIF).
- Archivo ilegible ⇒ `CorruptMediaError(source, reason)` — HU-009 lo capturará para la
  cuarentena; el pipeline no se cae.
- Tests contra los CA + capa secundaria etiquetada.

### 2.2 OUT — NO entra (delimitaciones)
- Cuarentena, reintentos y resumen de fallos → HU-009.
- Límite de dimensiones/memoria antes de decodificar → HU-011 (esta HU le deja el hueco).
- Lectura de EXIF → HU-004 · Detección de compresión WhatsApp → HU-007.
- **Decodificar** la imagen (obtener píxeles/dimensiones) → HU-011/HU-020; aquí solo se
  clasifica la firma.
- **Soportar** HEIC/AVIF: requeriría una dependencia nueva (p. ej. `pillow-heif`) ⇒ ADR +
  HU propia. Hoy se reconocen para poder rechazarlos con un mensaje útil.
- Formatos de video → HU-003 (depende del ADR de video, aún pendiente).

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | Extensión que miente (foto renombrada a `.txt`, o `.jpg` que es texto) | Manda el contenido: la foto se reconoce, el texto no | ticket ("magic bytes, no extensión") |
| 2 | Archivo más corto que la firma | Firma desconocida (`None`), sin excepción | `python.md` (fail safe en datos del usuario) |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- ¿TIFF entra en los soportados? → P-1. · ¿Qué hacer con HEIC a futuro? → P-2.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `src/media_optimizer/ingest/formats.py` | nuevo | bajo | ✅ no existe en `develop` (186ada5) |
| `src/media_optimizer/ingest/__init__.py` | modif (re-export) | bajo | ✅ leído — hoy exporta solo `scan_input_folder` |
| `tests/ingest/test_formats.py` | nuevo | bajo | ✅ no existe |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| `core.CorruptMediaError` (HU-161) | Sí | Encaja literal: "el archivo no se puede leer o decodificar", con `source` + `reason` |
| `media_optimizer.testing` (HU-166) | Sí | `encode_jpeg` da JPEG reales; `not_an_image` da bytes sin firma válida |
| `ImageFormat` como StrEnum | Sí (patrón) | Consistente con `MediaType`/`Verdict`/`Orientation` de `core/` |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| N/A — clasifica, no persiste | read (16 bytes por archivo) | — | N/A |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "**magic bytes, no extensión**" | ticket HU-002 | No | La extensión no participa en la decisión, ni siquiera como pista |
| RN-2 | "rechazo de imágenes-bomba **antes de decodificar**" | backlog HU-011 | No | La detección lee 16 bytes y nunca decodifica: HU-011 puede insertarse entre esta HU y la decodificación |
| RN-3 | "cuarentena **con causa**, pipeline sigue" | backlog HU-009 | No | Ilegible ⇒ `CorruptMediaError` con `source`+`reason`; formato desconocido ⇒ `None` (dato, no excepción) |
| RN-4 | "mensajes de error accionables" | backlog HU-136 · HU-161 | No | HEIC/AVIF se reconocen para poder decir "formato X no soportado", no "archivo inválido" |
| RN-5 | "El pipeline asume medios de **celular**" | charter §6.7 | No | El set soportado cubre lo que produce un celular y su reenvío por WhatsApp: JPEG (dominante), PNG (capturas), WebP (descargas) |
| RN-6 | Cero números mágicos → config o perfil | `python.md` | Parcial | Las firmas binarias son **constantes de formato** (parte del estándar del archivo), no umbrales de negocio: viven en una tabla del módulo, no en `config/` |
| RN-7 | Cobertura ≥80% módulo tocado | CLAUDE.md Pre-Flight | No | Evidencia `pytest --cov` al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | La ruta se puede abrir y leer | `CorruptMediaError` nombrando ruta y causa |
| V-2 | Un JPEG renombrado a `.txt` se detecta como JPEG | test lo garantiza |
| V-3 | Un `.jpg` que contiene texto NO se detecta como imagen | test lo garantiza |

---

## 6. Preguntas abiertas

### P-1 — ¿TIFF entra en los formatos soportados?
- **Categoría:** INFORMATIVA
- **Importa porque:** el build lockeado **sí** lo decodifica (verificado: `TIFF: build (ver 42 - 4.7.1)`), así que excluirlo es una decisión, no una limitación.
- **Va dirigida a:** @oscardacto (ratificable en el PR).
- **Mi mejor hipótesis:** no incluirlo — ningún celular lo produce y el charter fija el
  dispositivo de referencia; sumarlo sería soportar un caso sin usuario. Añadirlo después
  es una fila en la tabla de firmas + una entrada en el enum.
- **Si se asume mal, costo:** ~5 líneas.
- **Estado:** ABIERTA

### P-2 — ¿Se soportará HEIC en algún momento (fotos de iPhone)?
- **Categoría:** INFORMATIVA (para una HU futura, no para esta)
- **Importa porque:** si el negocio recibe material de iPhone, hoy quedaría fuera del
  pipeline con un mensaje de "convierte a JPEG".
- **Mi mejor hipótesis:** no en v1 — el cliente 0 usa Android (Redmi, charter §6.7) y
  soportarlo exige dependencia nueva con su ADR. Reconocerlo (esta HU) da el 80% del valor
  al costo de 3 líneas: el usuario sabe exactamente qué pasó.
- **Si se asume mal, costo:** HU nueva + ADR de dependencia (aditivo, sin rework).
- **Estado:** ABIERTA (transferida como nota de producto)

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Soportados = {JPEG, PNG, WebP} — **verificado** contra el build, no asumido | P-1 | Fila adicional en la tabla de firmas |
| A-2 | HEIC/AVIF reconocidos pero no soportados | P-2 | HU + ADR aditivos |
| A-3 | 16 bytes de cabecera bastan para todas las familias cubiertas | — | Ampliar la constante (interno) |
| A-4 | Formato desconocido es un **dato** (`None`), no una excepción: no es un error, es una clasificación | — | Cambio de firma (afectaría a HU-009) |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | Un archivo con firma JPEG válida pero contenido corrupto pasa la validación | técnico | alta | bajo | **Por diseño**: esta HU valida la firma, no la integridad; el truncado lo detecta la decodificación (HU-011/020) y lo gestiona HU-009. Documentado en el docstring para que nadie confunde "firma válida" con "imagen sana" |
| R-2 | Un re-lock futuro de OpenCV cambie qué formatos decodifica y el set soportado quede desactualizado | datos | baja | medio | Test que verifica que **cada** formato declarado soportado es realmente decodificable por el cv2 instalado — si un re-lock lo rompe, falla en CI, no en producción |
| R-3 | `SUPPORTED_FORMATS` mutado por un llamador | técnico | baja | bajo | `frozenset` |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (2 INFORMATIVAS)
- **Asunciones tomadas:** 4 (A-1 respaldada por verificación empírica)
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop 186ada5`: `ingest/` con scanner, 92 tests verdes)
  - [x] **Capacidades reales del stack verificadas ejecutando** `cv2.getBuildInformation()`
        y encode/decode: JPEG ✅ · PNG ✅ · WebP ✅ · TIFF ✅ · **AVIF: NO** · **HEIF ausente**
  - [x] Firmas binarias verificadas contra bytes reales generados por cv2 (`ffd8ffe0…`,
        `89504e470d0a1a0a…`, `52494646…57454250`)
  - [x] Consumidores cruzados en el backlog (HU-004/007/009/011 — insumo §2)
  - [x] Componentes reutilizables buscados (§3.1)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 92% — el 8%: P-1/P-2 (alcance de formatos, ambos aditivos y sin rework).

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-001 | Entrega las rutas a clasificar | DONE |
| HU-161 | Aporta `CorruptMediaError` | DONE |
| HU-166 | Aporta fixtures (JPEG real, bytes sin firma) | DONE |
| HU-004, HU-007, HU-009, HU-011, HU-017 | Consumen el veredicto | backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna.

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — Manda el contenido, no la extensión
- **Given:** un JPEG real guardado como `foto.txt`, y un archivo de texto guardado como `documento.jpg`
- **Then:** el primero se detecta `JPEG`; el segundo, `None`

### CA-2 — Formatos soportados reconocidos
- **Given:** archivos JPEG, PNG y WebP generados por el stack real
- **Then:** cada uno se detecta con su formato y `is_supported_image` es `True`

### CA-3 — Reconocido pero no soportado
- **Given:** cabeceras HEIC (`ftypheic`) y AVIF (`ftypavif`)
- **Then:** se detectan como `HEIC`/`AVIF`, pero `is_supported_image` es `False` — el llamador puede decir qué formato es

### CA-4 — Desconocido sin excepción
- **Given:** bytes sin firma válida y un archivo vacío
- **Then:** `detect_image_format` devuelve `None` en ambos casos, sin lanzar

### CA-5 — Archivo ilegible degrada con causa
- **Given:** una ruta que no se puede leer (inexistente)
- **Then:** `CorruptMediaError` cuyo mensaje nombra la ruta y la causa

### CA-6 — No decodifica ni carga el archivo entero
- **Given:** un archivo cuya cabecera es JPEG válida pero con basura después
- **Then:** se detecta `JPEG` igual (la validación es de firma, no de integridad) — comportamiento explícito, no accidental

### CA-7 — El set soportado corresponde al stack real
- **Given:** cada formato en `SUPPORTED_FORMATS`
- **Then:** el cv2 instalado lo codifica y decodifica de vuelta — si un re-lock lo rompe, este test falla

### CA-8 — No destructivo
- **Then:** los bytes y el `mtime` del archivo inspeccionado quedan idénticos

### CA-9 — Cobertura del módulo ≥80%
- **Then:** `pytest --cov=media_optimizer.ingest` ≥ 80%

### CA-10 — Batería completa verde
- **Then:** pytest · ruff check + format --check · mypy, todo exit 0

### CA-11 — Trazabilidad
- **Then:** gate-log con `draft`, `gate_spec`, `dev` de HU-002

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial, verificación empírica del stack y evaluación de gate | Claude (ejecutor) |
