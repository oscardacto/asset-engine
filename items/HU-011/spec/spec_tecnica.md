# Spec Técnica `HU-011` — `Límites de memoria y dimensiones: rechazo de imágenes-bomba antes de decodificar`

> **Estado:** LISTA PARA DEV
> **Fecha de generación:** 2026-07-26
> **Última actualización:** 2026-07-26
> **Confianza global:** 90% — ver sección 9

---

## 1. Resumen ejecutivo

- **Qué se pide:** conocer cuánta memoria pediría un archivo al abrirse, **sin abrirlo**, y
  apartar el que pida una cantidad desproporcionada.
- **Para quién:** la seguridad del pipeline (una imagen-bomba tumbaría el proceso entero) y,
  como efecto colateral valioso, HU-005 (orientación), HU-008 ("bajo el nativo") y HU-018
  (reporte de inventario), que necesitan las dimensiones sin pagar una decodificación.
- **Módulo / dominio:** `media_optimizer.ingest` — módulo nuevo `dimensions.py` + una causa
  nueva en el registro de cuarentena de HU-009. Cobertura exigida ≥80%.
- **No obvio (lo crítico que el ticket no dice de frente):** el umbral no se puede elegir
  por intuición. El celular de referencia del cliente 0 (Redmi Note 13 Pro+) tiene sensor
  de **200 MP**: una foto legítima suya ocupa ~600 MB decodificada y **superaría el límite
  por defecto de librerías conocidas** (Pillow avisa a partir de ~89 MP). Un umbral
  "razonable" descartaría material real del cliente. El límite debe expresarse en **memoria
  estimada**, no en píxeles "que suenan muchos".

---

## 2. Alcance

### 2.1 IN — entra en este WorkItem
- `ingest/dimensions.py`:
  - `ImageSize` (frozen): `width`, `height` + `pixels`, `longest_side`,
    `estimated_decoded_bytes` (3 bytes/píxel, que es lo que reserva OpenCV en BGR).
  - `read_image_size(path, image_format) -> ImageSize | None` — de la cabecera, sin
    decodificar. Cubre los tres formatos soportados:
    - **PNG**: chunk `IHDR` en posición fija (verificado).
    - **JPEG**: recorrido de segmentos hasta el marcador `SOF` (no está en posición fija).
    - **WebP**: las tres variantes `VP8X` / `VP8L` / `VP8 ` (nuestro cv2 produce **VP8L**,
      verificado — asumir solo la variante con pérdida habría fallado en nuestros propios
      fixtures).
  - `MAX_DECODED_BYTES`, `MAX_SIDE`: constantes nombradas, promovibles a `config/` (HU-155).
- Integración con el registro de HU-009: nueva causa `QuarantineReason.TOO_LARGE` con
  detalle accionable (cuánto pide y cuál es el máximo).
- Refactor menor de `quarantine._classify` para que la cadena de comprobaciones siga
  legible al sumar la quinta (extracción de `_find_problem`).
- Tests contra los CA + capa secundaria etiquetada.

### 2.2 OUT — NO entra (delimitaciones)
- **Decodificar** la imagen → sigue siendo de la etapa de análisis (E2).
- Presupuesto de rendimiento por etapa y memoria pico real → HU-165 (`benchmarks/`).
- Flag "bajo el nativo" (resolución insuficiente para el formato de salida) → HU-008: usa
  la misma primitiva pero compara contra el perfil, no contra un límite de seguridad.
- Orientación V/H → HU-005 (necesita además EXIF Orientation).
- Externalizar el umbral a `config/` → HU-155.
- Dimensiones de video → HU-014.

### 2.3 Casos límite mencionados en el ticket
| # | Caso | Tratamiento esperado | Fuente |
|---|---|---|---|
| 1 | Archivo pequeño que declara dimensiones enormes | Apartado sin decodificar | ticket (imagen-bomba) |
| 2 | Foto legítima de altísima resolución (200 MP del equipo de referencia) | **Aceptada** | charter §6.7 |

### 2.4 Casos límite NO mencionados (van a §6 como preguntas)
- Valor concreto del umbral → P-1. · Qué hacer si no se pueden leer las dimensiones → P-2.

---

## 3. Componentes técnicos identificados

| Componente | Tipo cambio | Riesgo | Verificado en la rama principal |
|---|---|---|---|
| `src/media_optimizer/ingest/dimensions.py` | nuevo | medio (parser de 3 formatos) | ✅ no existe en `develop` (0c6b2bf) |
| `src/media_optimizer/ingest/quarantine.py` | modif (causa nueva + refactor de la cadena) | bajo | ✅ leído — 5 causas, `_classify` con 4 comprobaciones |
| `src/media_optimizer/ingest/__init__.py` | modif (re-export) | bajo | ✅ leído — 13 nombres |
| `tests/ingest/test_dimensions.py` | nuevo | bajo | ✅ no existe |

### 3.1 Componentes reutilizables ya existentes
| Componente existente | ¿Reutilizar? | Justificación |
|---|---|---|
| `QuarantineReason` / `QuarantinedAsset` (HU-009) | Sí | La HU es la primera prueba real de que el registro admite causas nuevas sin rediseño |
| `quarantine._read_bytes` (HU-009) | Sí | Ya convierte `OSError` en `CorruptMediaError`; leer cabecera es el mismo patrón |
| `ImageFormat` (HU-002) | Sí | El parser se selecciona por el formato ya detectado, sin volver a mirar la firma |
| `media_optimizer.testing` (HU-166) | Sí | Genera imágenes reales de dimensiones conocidas para verificar el parser |

---

## 4. Modelo de datos

### 4.1 Entidades/tablas tocadas
| Entidad | Operación | Campos afectados | Verificado contra el esquema real |
|---|---|---|---|
| `ImageSize` (en memoria) | nuevo tipo | width, height | N/A |
| `QuarantineReason` | valor nuevo (`TOO_LARGE`) | — | ✅ verificado: es un StrEnum, ampliarlo no rompe a los consumidores existentes |

### 4.2 Migraciones/cambios de esquema requeridos
- [ ] Sí
- [x] No

---

## 5. Reglas de negocio

| # | Regla literal | Fuente | ¿Ambigua? | Implicación técnica |
|---|---|---|---|---|
| RN-1 | "rechazo de imágenes-bomba **antes de decodificar**" | ticket | No | Solo se leen bytes de cabecera; jamás se llama a `cv2.imdecode` |
| RN-2 | "El pipeline asume medios de **celular**" (200 MP en el equipo de referencia) | charter §6.7 | No | El umbral admite ≥200 MP; se expresa en memoria estimada, no en píxeles sueltos |
| RN-3 | "Cero números mágicos — umbrales […] van a `config/`" | `python.md` | Parcial | `config/` no existe (HU-155): constantes nombradas y documentadas como promovibles |
| RN-4 | "un archivo corrupto degrada ese asset, nunca tumba el pipeline" | `python.md` | No | Reutiliza el registro de cuarentena; el lote sigue |
| RN-5 | "Entradas hostiles se validan antes de procesar […] tamaños" | `python.md` | No | Esta HU es literalmente esa validación |
| RN-6 | "mensajes de error accionables" | backlog HU-136 | No | El detalle dice cuánto pide el archivo y cuál es el máximo, no solo "demasiado grande" |
| RN-7 | Cobertura ≥80% módulo tocado | CLAUDE.md Pre-Flight | No | Evidencia `pytest --cov` al cierre |

### 5.1 Validaciones derivadas
| # | Validación | Si falla |
|---|---|---|
| V-1 | Las dimensiones leídas coinciden con las reales de una imagen generada | test lo garantiza en los 3 formatos |
| V-2 | Una cabecera que declara dimensiones absurdas se aparta sin decodificar | test lo garantiza (archivo de pocos bytes) |
| V-3 | Una foto de 200 MP se acepta | test lo garantiza (cabecera sintética, sin generar la imagen real) |

---

## 6. Preguntas abiertas

### P-1 — ¿Cuál es el umbral exacto?
- **Categoría:** INFORMATIVA
- **Importa porque:** demasiado bajo descarta fotos legítimas del cliente; demasiado alto
  no protege.
- **Va dirigida a:** @oscardacto (ratificable con la integración).
- **Mi mejor hipótesis:** **1 GiB de memoria estimada** (≈358 MP) y **65.535 px de lado**
  (el máximo que el propio formato JPEG admite). Con eso, una foto de 200 MP del equipo de
  referencia (~600 MB) pasa con margen, y un PNG que declare 60.000 × 60.000 (~10 GB) se
  aparta. El límite protege contra lo absurdo; el coste de procesar una foto grande pero
  legítima es asunto del presupuesto de rendimiento (HU-165), no de este chequeo.
- **Si se asume mal, costo:** cambiar una constante (y en HU-155, un valor de configuración).
- **Estado:** ABIERTA

### P-2 — ¿Qué se hace si no se pueden leer las dimensiones de la cabecera?
- **Categoría:** INFORMATIVA
- **Mi mejor hipótesis:** aceptar (fail-safe), igual que en la comprobación de truncamiento
  de HU-009: no se aparta material por no poder medirlo. El archivo ya pasó firma y cierre;
  si además fuera una bomba, la decodificación fallará y quedará registrada allí.
- **Si se asume mal, costo:** ninguno inmediato; endurecerlo sería cambiar una rama.
- **Estado:** ABIERTA

---

## 7. Asunciones explícitas

| # | Asunción | Cubre pregunta | Costo si se rompe |
|---|---|---|---|
| A-1 | `MAX_DECODED_BYTES` = 1 GiB · `MAX_SIDE` = 65.535 px | P-1 | Cambiar constantes |
| A-2 | Dimensiones ilegibles ⇒ se acepta (fail-safe) | P-2 | Cambiar una rama |
| A-3 | 3 bytes por píxel para estimar la memoria (BGR de OpenCV) | — | Ajustar el factor; el orden de magnitud no cambia |
| A-4 | 64 KiB de cabecera bastan para hallar el `SOF` de un JPEG (los EXIF con miniatura empujan el marcador, pero no tanto) | — | Ampliar la constante de lectura |
| A-5 | La memoria estimada es del **bitmap decodificado**, no el pico real del decodificador (que puede ser mayor) | — | Es una cota inferior deliberada: protege contra lo absurdo, no sustituye a HU-165 |

---

## 8. Riesgos identificados

| # | Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|---|
| R-1 | Parser de JPEG que no encuentra el `SOF` en un archivo válido (EXIF grande, segmentos raros) | técnico | media | bajo | Devuelve `None` ⇒ se acepta (A-2); tests con JPEG real de nuestro generador + con relleno EXIF |
| R-2 | Umbral que descarta una foto legítima del cliente | datos | baja | **alto** | Test explícito con una cabecera de 200 MP que debe aceptarse; el umbral se fijó a partir del equipo de referencia, no de la intuición |
| R-3 | Parser mal implementado que lee dimensiones erróneas y aparta material bueno | técnico | media | alto | Los tests comparan contra imágenes generadas de dimensiones conocidas en los 3 formatos, incluidas dimensiones asimétricas (96×48) para detectar ancho/alto intercambiados |

---

## 9. Confianza global y recomendación

- **Preguntas abiertas:** 2 total — **0 bloqueantes** (2 INFORMATIVAS)
- **Asunciones tomadas:** 5
- **Verificaciones cruzadas:**
  - [x] Codebase actual leído (`develop 0c6b2bf`: `ingest/` con 4 módulos, 143 tests verdes)
  - [x] **Layout real de cabeceras verificado ejecutando** sobre bytes generados por cv2:
        PNG `IHDR` en 12:16 con dimensiones en 16:24 · JPEG arranca con `FFD8 FFE0` (SOF no
        está en posición fija) · WebP de cv2 resultó ser **VP8L**, no la variante con pérdida
  - [x] Extensibilidad del registro de HU-009 verificada en el código (StrEnum ampliable)
  - [x] Dispositivo de referencia cruzado con el charter (200 MP condiciona el umbral)
  - [x] Componentes reutilizables buscados (§3.1)
- **Recomendación:**
  - [x] ✅ LISTA PARA DEV (preguntas bloqueantes = 0 · confianza ≥ 85%)
  - [ ] ⚠️ REQUIERE REFINAMIENTO ADICIONAL
  - [ ] ❌ NO VIABLE TAL COMO ESTÁ
- **Confianza:** 90% — el 10%: R-1/R-3 (los parsers son la parte con más superficie de error de todas las HUs hasta ahora) y P-1.

---

## 10. Dependencias

### 10.1 Otros WorkItems (orden de despliegue)
| ID | Relación | Estado |
|---|---|---|
| HU-002 | Aporta el formato ya detectado | DONE |
| HU-009 | Aporta el registro de cuarentena que se amplía | DONE |
| HU-166 | Aporta imágenes de dimensiones conocidas | DONE |
| HU-005, HU-008, HU-018 | Reutilizarán `read_image_size` | backlog |
| HU-155 | Externalizará el umbral | backlog |
| HU-165 | Presupuesto de rendimiento (complementario, no sustituto) | backlog |

### 10.2 Datos/configuración previa requerida
- Ninguna.

### 10.3 Servicios o equipos externos
- Ninguno.

---

## 11. Criterios de aceptación (Given/When/Then)

### CA-1 — Dimensiones correctas en los tres formatos
- **Given:** una imagen de 96 × 48 generada en JPEG, PNG y WebP
- **Then:** `read_image_size` devuelve 96 × 48 en los tres (asimétrica a propósito: detecta ancho/alto intercambiados)

### CA-2 — Se lee sin decodificar
- **Given:** un archivo con cabecera válida que declara 60.000 × 60.000 pero solo pesa unos bytes
- **Then:** se obtienen esas dimensiones y el archivo se aparta — sin que el proceso reserve memoria

### CA-3 — La imagen-bomba se aparta con causa
- **Given:** el archivo anterior en un lote junto a una foto normal
- **Then:** la foto se acepta, la bomba queda apartada con `TOO_LARGE`, y el detalle indica cuánta memoria pediría y cuál es el máximo

### CA-4 — Una foto legítima de alta resolución se acepta
- **Given:** una cabecera PNG que declara ~200 MP (equipo de referencia del cliente)
- **Then:** se acepta

### CA-5 — Límite por lado
- **Given:** una cabecera que declara 70.000 px de lado con pocos píxeles totales
- **Then:** se aparta por exceder el máximo por lado

### CA-6 — Dimensiones ilegibles no descartan material
- **Given:** un archivo cuya cabecera no permite determinar dimensiones
- **Then:** `read_image_size` devuelve `None` y el triaje lo acepta

### CA-7 — Las causas anteriores siguen intactas
- **Then:** los 15 tests de HU-009 siguen pasando sin cambios (la ampliación no rompe el contrato previo)

### CA-8 — No destructivo
- **Then:** bytes y `mtime` de los archivos quedan idénticos

### CA-9 — Cobertura del módulo ≥80%
- **Then:** `pytest --cov=media_optimizer.ingest` ≥ 80%

### CA-10 — Batería completa verde
- **Then:** pytest · ruff check + format --check · mypy, todo exit 0

### CA-11 — Trazabilidad
- **Then:** gate-log con `draft`, `gate_spec`, `dev` de HU-011

---

## 12. Historial de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-07-26 | Creación inicial, verificación empírica de cabeceras y evaluación de gate | Claude (ejecutor) |
| 2026-07-26 | DEV: implementado según §2.1 (A-1…A-5 aplicadas). Refinamiento sobre la spec: se eliminó una rama muerta de `_is_truncated` (el `.get()` nunca podía devolver `None` para un formato soportado) sustituyéndola por acceso directo, que falla ruidosamente si algún día se añade un formato sin marca de cierre. Batería 167 tests verde, ingest/ 100% | Claude (ejecutor) |
