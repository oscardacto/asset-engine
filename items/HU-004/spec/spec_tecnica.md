# Spec Técnica `HU-004` — `Lectura segura de EXIF: malformado o ausente degrada el asset, no tumba el lote`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 89% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** leer los metadatos EXIF de una foto de forma que ningún bloque
  malformado, truncado o ausente pueda detener el lote.
- **Para quién:** HU-005 (orientación V/H), HU-015 (agrupación por sesión de captura),
  HU-018 (reporte de inventario).
- **Módulo / dominio:** `media_optimizer.ingest` — módulo nuevo `exif.py`. Cobertura ≥80%.
- **No obvio (lo crítico que el ticket no dice de frente):** la orientación EXIF **no es
  un dato pasivo**. Verificado sobre el stack real: OpenCV **rota la imagen al decodificar**
  si el EXIF lo indica (una foto de 48×96 con `Orientation=6` vuelve como 96×48), mientras
  las dimensiones de cabecera que lee HU-011 siguen siendo las crudas. Si el pipeline no es
  explícito sobre qué dimensiones usa, el reporte de inventario y la detección V/H pueden
  contradecirse entre sí. Esta HU debe **exponer esa diferencia**, no esconderla.

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- `ingest/exif.py`:
  - `ExifOrientation` (IntEnum 1–8) con la propiedad `swaps_axes` (cierto para 5–8, los
    valores que intercambian ancho y alto).
  - `ExifData` (frozen): `orientation: ExifOrientation | None`,
    `captured_at: datetime | None`, `is_present: bool`, `is_malformed: bool`.
  - `read_exif(path) -> ExifData` — **nunca lanza** por EXIF inválido: devuelve el dato
    parcial que haya podido leerse y marca `is_malformed`.
  - `oriented_size(size, orientation) -> ImageSize` — aplica el intercambio de ejes a unas
    dimensiones crudas, para que quien necesite las dimensiones *visibles* las obtenga sin
    decodificar.
- Parser propio de la estructura TIFF/IFD (orden de bytes, entradas, puntero al sub-IFD),
  con límites explícitos contra EXIF hostil (número de entradas, desplazamientos fuera de
  rango, recursión).
- Tests contra los CA + capa secundaria etiquetada.

### 2.2 OUT — NO entra (delimitaciones)
- Decidir la orientación V/H del asset → **HU-005** (combina dimensiones + este dato).
- Agrupar por sesión de captura → HU-015 (consume `captured_at`).
- Flag de PII / GPS → HU-034. **Esta HU no lee GPS a propósito**: leer coordenadas sin una
  política de tratamiento sería recolectar PII sin necesidad.
- Escribir o corregir EXIF en las salidas → E4/E6 (el charter obliga a no tocar originales).
- Metadatos de video → HU-014.

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | EXIF **ausente** | `ExifData` vacío con `is_present=False`; el asset sigue | ticket |
| 2 | EXIF **malformado** | Lo que se pudo leer + `is_malformed=True`; sin excepción | ticket |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- ¿Qué campos concretos se leen? → P-1. · ¿Fechas EXIF sin zona horaria? → P-2.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `src/media_optimizer/ingest/exif.py` | nuevo | medio (parser binario de estructura anidada) | ✅ no existe en `develop` (23f29b3) |
| `src/media_optimizer/ingest/__init__.py` | modif (re-export) | bajo | ✅ leído — 18 nombres |
| `tests/ingest/test_exif.py` | nuevo | bajo | ✅ no existe |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| `cv2.imencodeWithMetadata` (OpenCV 5) | Sí, **en tests** | Permite fabricar fixtures con EXIF real sin dependencia nueva — verificado con ida y vuelta byte a byte |
| `ImageSize` (HU-011) | Sí | `oriented_size` opera sobre él; evita un tipo paralelo |
| `quarantine._read_bytes` / patrón de lectura acotada | Sí (patrón) | Misma política de leer solo lo necesario |
| `CorruptMediaError` (HU-161) | **No para EXIF inválido** | Un EXIF roto no invalida la foto: degrada el metadato, no el asset. Se reserva la excepción para el archivo ilegible |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| `ExifData` / `ExifOrientation` (en memoria) | nuevos tipos | orientation, captured_at, is_present, is_malformed | N/A |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "malformado o ausente **degrada el asset, no tumba el lote**" | ticket | No | `read_exif` no propaga excepciones por contenido EXIF; solo el archivo ilegible es error |
| RN-2 | "Entradas hostiles se validan antes de procesar […] EXIF" | `python.md` | No | Límites explícitos: nº de entradas, desplazamientos dentro del bloque, un solo nivel de sub-IFD |
| RN-3 | "orientación" es dato auditado por foto | Maestro §8.2 · backlog HU-005 | No | La orientación se expone tipada, no como entero suelto |
| RN-4 | Los medios pueden contener PII; procesamiento local | charter §6.6 | No | No se lee GPS en esta HU (ver §2.2); nada sale de la máquina |
| RN-5 | Determinismo | charter §6.1 | No | El parser no depende de orden de iteración ni de estado global |
| RN-6 | Cobertura ≥80% módulo tocado | CLAUDE.md Pre-Flight | No | Evidencia `pytest --cov` al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | Un EXIF truncado a la mitad no lanza excepción | test lo garantiza |
| V-2 | Un `Orientation` fuera de 1–8 se ignora en vez de aceptarse | test lo garantiza |
| V-3 | Un desplazamiento de sub-IFD fuera del bloque no provoca lectura fuera de rango | test lo garantiza |

---

## 6. Preguntas abiertas

### P-1 — ¿Qué campos EXIF se leen en esta HU?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** solo los que tienen consumidor declarado en el backlog:
  `Orientation` (HU-005) y `DateTimeOriginal` (HU-015). Leer el resto sería inventariar
  metadatos sin usuario, y en el caso de GPS sería además recolectar PII sin política.
- **Si se asume mal, costo:** añadir un campo es una entrada más en la tabla de etiquetas.
- **Estado:** ABIERTA

### P-2 — ¿Cómo se trata una fecha EXIF sin zona horaria?
- **Categoría:** INFORMATIVA
- **Importa porque:** el formato EXIF `YYYY:MM:DD HH:MM:SS` no lleva zona; interpretarla
  como UTC o como local cambia la agrupación por sesión de HU-015.
- **Mi mejor hipótesis:** `datetime` **ingenuo** (sin zona), tal como viene. Inventar una
  zona sería añadir información que el archivo no tiene; HU-015 agrupa por diferencias
  relativas, donde la zona es irrelevante mientras sea consistente.
- **Si se asume mal, costo:** HU-015 aplicaría la conversión que decida.
- **Estado:** ABIERTA (transferida a HU-015)

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | Solo `Orientation` y `DateTimeOriginal` | P-1 | Entrada adicional en la tabla |
| A-2 | Fechas como `datetime` ingenuo | P-2 | Conversión en HU-015 |
| A-3 | Un solo nivel de sub-IFD (EXIF IFD); no se siguen punteros anidados más profundos | — | Ningún campo objetivo vive más profundo |
| A-4 | EXIF inválido ⇒ dato degradado, **no** `CorruptMediaError` | — | Cambiaría la política de cuarentena, no el parser |
| A-5 | Se lee la cabecera ya acotada (64 KiB) que usa el resto de la ingesta | — | Un EXIF gigantesco quedaría parcialmente leído y marcado como malformado |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | Parser binario con lectura fuera de rango ante EXIF hostil | seguridad | media | alto | Todos los accesos acotados al bloque; tests con desplazamientos inválidos, contadores absurdos y truncamientos |
| R-2 | Discrepancia silenciosa entre dimensiones de cabecera y decodificadas | datos | **alta** | alto | `oriented_size` explícito + documentación del comportamiento; HU-005 decidirá cuál usa y por qué |
| R-3 | Bucle infinito por punteros circulares de IFD | técnico | baja | alto | Un solo nivel de sub-IFD (A-3): estructuralmente imposible ciclar |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (2 INFORMATIVAS)
- **Asunciones tomadas:** 5
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop 23f29b3`: `ingest/` con 5 módulos, 167 tests verdes)
  - [x] **Capacidad real del stack verificada ejecutando**: OpenCV 5 lee y escribe EXIF
        (ida y vuelta byte a byte), y **aplica la rotación al decodificar** (tabla en el insumo)
  - [x] **Asunción previa invalidada**: A-2 de HU-166 ("cv2 no escribe EXIF; hará falta
        dependencia con ADR") es **falsa** en OpenCV 5 — no hace falta ni dependencia ni ADR
  - [x] Consumidores cruzados en el backlog (HU-005/015/018) y delimitación con HU-034 (PII)
  - [x] Componentes reutilizables buscados (§3.1)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 89% — el 11%: R-1 (parser binario, la superficie más delicada del proyecto hasta ahora) y R-2 (la discrepancia de dimensiones, que se expone pero la resuelve HU-005).

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-002, HU-011, HU-161, HU-166 | Aportan formato, `ImageSize`, errores y fixtures | DONE |
| HU-005 | Primer consumidor (orientación V/H) | backlog — siguiente natural |
| HU-015, HU-018 | Consumen `captured_at` y el reporte | backlog |
| HU-034 | Cubrirá GPS/PII, deliberadamente fuera de aquí | backlog |
| HU-166 | **Su asunción A-2 queda corregida por esta HU** | DONE |

### 10.2 Datos/configuración previa requerida
- Ninguna.

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — EXIF ausente no rompe nada
- **Given:** un JPEG sin EXIF
- **Then:** `ExifData` con `is_present=False`, sin orientación ni fecha, y sin excepción

### CA-2 — Orientación leída correctamente
- **Given:** JPEG con `Orientation` 1, 6 y 8
- **Then:** se lee el valor tipado correspondiente en cada caso

### CA-3 — EXIF malformado degrada, no tumba
- **Given:** un bloque EXIF truncado a la mitad, y otro con un contador de entradas absurdo
- **Then:** `is_malformed=True`, sin excepción, y el asset sigue siendo utilizable

### CA-4 — Valores inválidos se ignoran
- **Given:** `Orientation = 99`
- **Then:** `orientation is None` y `is_malformed=True` — no se acepta un valor fuera de rango

### CA-5 — Fecha de captura
- **Given:** un EXIF con `DateTimeOriginal = "2026:04:04 15:30:00"`
- **Then:** `captured_at` es el `datetime` correspondiente; una fecha con formato inválido deja `captured_at=None` y marca malformado

### CA-6 — La discrepancia de dimensiones queda explícita
- **Given:** dimensiones crudas 48×96 y `Orientation=6`
- **Then:** `oriented_size` devuelve 96×48; con `Orientation=1` devuelve 48×96 sin cambios

### CA-7 — Robustez ante EXIF hostil
- **Given:** desplazamiento de sub-IFD fuera del bloque, y número de entradas enorme
- **Then:** no hay excepción, no hay lectura fuera de rango, y el resultado queda marcado como malformado

### CA-8 — No destructivo
- **Then:** bytes y `mtime` del archivo quedan idénticos tras leer el EXIF

### CA-9 — Cobertura del módulo ≥80%
- **Then:** `pytest --cov=media_optimizer.ingest` ≥ 80%

### CA-10 — Batería completa verde
- **Then:** pytest · ruff check + format --check · mypy, todo exit 0

### CA-11 — Trazabilidad
- **Then:** gate-log con `draft`, `gate_spec`, `dev` de HU-004

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial, verificación empírica del stack y evaluación de gate | Claude (ejecutor) |
