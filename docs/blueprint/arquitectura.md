# Arquitectura — media-optimizer

> Documento de la constitución del proyecto, junto al charter y el backlog.
> Fija **qué depende de qué** y por qué. Las decisiones puntuales viven en `adr/`.

---

## 1. Principio rector: hexagonal ligera

El dominio no sabe de dónde vienen los datos ni a dónde van. Todo lo que toca el mundo
exterior —disco, formatos de imagen, línea de comandos— es una **capa de adaptación**:
traduce entre el mundo exterior y los contratos internos, y no decide nada.

Consecuencia práctica: se puede cambiar la librería de la CLI, el formato del catálogo o la
biblioteca de visión sin tocar una sola regla de negocio.

---

## 2. Diagrama de dependencias

Las flechas se leen **"depende de"**. No hay ninguna flecha que suba.

```
                      ┌──────────────────────────────┐
   MUNDO EXTERIOR     │   argparse · sys.argv · disco │
                      └───────────────┬──────────────┘
                                      │
   ═══════════════════════════════════│═══════════════════════════════
   CAPAS DE ADAPTACIÓN                ▼
                      ┌──────────────────────────────┐
                      │  cli/                        │  traduce argumentos → contratos
                      │  cli/commands/               │  ÚNICO lugar que importa argparse
                      │  run · report · label        │  tres capacidades, no una por etapa
                      └───────┬──────────────┬───────┘
                              │              │ consulta qué etapas
                              │              │ y qué reportes existen
                              │              ▼
                              │   ┌────────────────────────┐
                              │   │ pipeline/registry.py   │  las etapas son DATOS
                              │   └────────────────────────┘
                              ▼
                      ┌──────────────────────────────┐
                      │  pipeline/                   │  orquesta etapas, degrada fallos
                      └───────────────┬──────────────┘
                                      │
          ┌───────────────┬───────────┼───────────┬──────────────┐
          ▼               ▼           ▼           ▼              ▼
    ┌──────────┐   ┌──────────┐ ┌─────────┐ ┌─────────┐   ┌──────────┐
    │ ingest/  │   │  photo/  │ │ video/  │ │profiles/│   │ workspace│
    │          │   │          │ │         │ │         │   │  · logs  │
    └────┬─────┘   └────┬─────┘ └────┬────┘ └────┬────┘   └────┬─────┘
         │              │            │           │             │
         │              └────────┬───┘           │             │
         │                       ▼               │             │
         │              ┌────────────────┐       │             │
         │              │    vision/     │       │             │
         │              └────────┬───────┘       │             │
         │                       │               │             │
   ══════│═══════════════════════│═══════════════│═════════════│═══════
   DOMINIO PURO                  ▼               ▼             ▼
                      ┌──────────────────────────────┐
                      │  core/     ·     ranking/    │  cero IO · cero terceros
                      └──────────────────────────────┘

   ingest/ es la ÚNICA capa que toca el disco físico, a través de
   ingest/filesystem.py — ver ADR-004.
```

### Reglas que el diagrama impone

| # | Regla | Verificada por |
|---|-------|----------------|
| A-1 | `core/` y `ranking/` no importan nada de infraestructura: ni `os`, ni `shutil`, ni `cv2`, ni `numpy`, ni `media_optimizer.ingest` | `tests/test_arquitectura.py::test_el_dominio_puro_no_importa_nada_de_infraestructura` |
| A-2 | **`core/` nunca depende de `argparse`** | mismo test, ampliado (HU-162) |
| A-3 | Todo acceso físico al disco pasa por `ingest/filesystem.py` | `tests/test_arquitectura.py::test_ningun_modulo_de_produccion_toca_el_disco_por_su_cuenta` · ADR-004 |
| A-4 | **`argparse` solo se importa dentro de `cli/`** | test nuevo (HU-162) |
| A-5 | Ningún contrato de `core/` expone una colección sin orden | `tests/core/test_determinism.py::TestGuardianDeContratos` · HU-169 |
| A-6 | **`cli/` no contiene listas de etapas ni de reportes escritas a mano**: se las pide al registro | test nuevo (HU-162) |

Ninguna de estas reglas es una convención escrita: **todas fallan la batería si se violan.**

---

## 3. La CLI es una capa de adaptación

Fijado por ADR-005. La CLI hace exactamente tres cosas, en este orden:

```
   argumentos de texto  →  [ 1. parsear ]  →  Namespace sin tipos
                        →  [ 2. validar y convertir ]  →  dataclass congelado
                        →  [ 3. invocar el dominio ]  →  resultado
                        →  [ 4. traducir a texto y código de salida ]
```

**Lo que la CLI no hace, sin excepción:**

- **No contiene lógica de negocio.** Ni un umbral, ni un peso, ni un criterio de descarte.
  Si un comando necesita decidir algo, ese algo pertenece a un módulo del dominio.
- **No toca el disco directamente.** Va por la capa de ADR-004, como todos.
- **No propaga sus tipos hacia adentro.** El dominio recibe dataclasses propios; nunca un
  `Namespace`, nunca un tipo de la librería de parseo.
- **No formatea la salida persistida.** Lo que se escribe a archivo lo genera código propio
  y se compara byte a byte en golden tests. La CLI solo escribe a la consola.

**Prueba de que la separación es real:** el dominio completo debe poder ejercitarse desde los
tests sin importar `cli/` ni `argparse` — y así es hoy, con 422 tests y sin CLI existente.

### 3.1 Las etapas son datos, no comandos

La CLI expone **tres capacidades**, no una por etapa del pipeline:

```
run     <etapa>     ingest · analyze · develop · select · reel · all
report  <tipo>      inventory · analysis · develop · selection · reel · run · history
label
```

`<etapa>` y `<tipo>` son **argumentos posicionales** cuyos valores válidos salen de
`pipeline/registry.py`. No son subcomandos anidados: toda etapa recibe lo mismo —workspace,
perfil y opcionalmente un origen— porque **sus parámetros son datos del perfil de negocio**,
nunca banderas de línea de comandos. Un `--clahe-clip` sería criterio estético fuera del
perfil, justo el `if` por cliente que el charter §3 prohíbe.

Es la misma regla que el charter fijó para los perfiles, aplicada a las etapas: **una etapa
no es una capacidad distinta del sistema, es material de trabajo del orquestador.**

**Consecuencia que sostiene la decisión:** añadir una etapa o un reporte es añadir una
entrada al registro. `cli/` no se toca, y el parser no crece con el producto — que es lo que
mantiene válida la elección de `argparse` (ADR-005) más allá de su umbral de reapertura.

---

## 4. Módulos

| Módulo | Propósito | Capa |
|--------|-----------|------|
| `core/` | Contratos del dominio: `MediaAsset`, `QualityReport`, `Transform`, `StageReport`, `BusinessProfile`, errores, determinismo | Dominio puro |
| `ranking/` | Score global, portada, orden narrativo, cobertura | Dominio puro |
| `vision/` | Primitivas de visión compartidas | Adaptación (OpenCV) |
| `ingest/` | Escaneo, validación, catálogo · **`filesystem.py` es la única puerta al disco** | Adaptación (disco) |
| `photo/` · `video/` | Análisis y revelado · escenas y reels | Adaptación |
| `profiles/` | Perfiles de negocio como datos + carga y validación | Adaptación |
| `workspace` | Directorio de trabajo, nombres escribibles, verificación de no-destructividad | Adaptación (nivel superior: lo usan todas las etapas) |
| `logs` | Rastro estructurado JSON lines | Adaptación (nivel superior, misma razón) |
| `pipeline/` | Orquestación, degradación de fallos, observabilidad | Adaptación |
| `cli/` | **Traduce argumentos a contratos internos. Nada más.** | Adaptación |
| `config/` | Configuración externalizada | Adaptación |
| `testing/` | Generadores de datos sintéticos | Soporte de pruebas |

---

## 5. Decisiones de arquitectura vigentes

| ADR | Decisión | Estado |
|-----|----------|--------|
| [ADR-001](adr/ADR-001-gestor-entorno.md) | `uv` como gestor de entorno y dependencias | Aceptado |
| [ADR-002](adr/ADR-002-stack-vision.md) | `opencv-python-headless` + NumPy | Aceptado |
| [ADR-003](adr/ADR-003-catalogo-local.md) | Catálogo en JSON con claves ordenadas | Aceptado |
| [ADR-004](adr/ADR-004-acceso-al-filesystem.md) | Capa única de acceso al filesystem + identidad por contenido | Aceptado |
| [ADR-005](adr/ADR-005-framework-cli.md) | `argparse` con frontera tipada | Aceptado |

## 6. Dependencias de producción

**Dos.** `numpy` y `opencv-python-headless`. La CLI no añade ninguna (ADR-005).

Toda dependencia nueva que reciba rutas debe medirse contra la matriz de casos hostiles de
ADR-004 antes de adoptarse — no es paranoia: `logging.FileHandler` de la biblioteca estándar
la falla, y descarta registros en silencio (medido en HU-156).
