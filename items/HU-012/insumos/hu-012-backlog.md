# HU-012 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E1 (commit `f10d05e`):

> | HU-012 | Persistencia del catálogo (según ADR HU-153) con **escritura atómica** | Depende de: HU-153, HU-157 | P0 | M |

Dependencias satisfechas: HU-153 **DONE** (ADR-003 Aceptado) y HU-157 **DONE**
(`MediaAsset`).

## 2. Quiénes consumen el catálogo (dicta qué campos debe llevar)

Fuente: `docs/blueprint/backlog.md`:

> | HU-013 | **Re-ingesta idempotente: mismo input no duplica ni reprocesa** | HU-012 |
> | HU-016 | Directorio de trabajo no destructivo: layout de salidas + verificación de que el origen queda intacto | HU-012 |
> | HU-017 | CLI `ingest`: carpeta → catálogo + resumen en consola | HU-162, HU-012 |
> | HU-018 | Reporte de inventario del lote (tabla por asset: **dims, orientación, flags** — formato Maestro §8.2) | HU-017 |
> | HU-019 | Sidecar de etiquetas manuales (ambiente, descarte, notas) que **sobrevive re-ingestas** | HU-013 |
> | HU-035 | `QualityReport` agregado y serializado al catálogo | HU-030 |
> | HU-182 | Reanudación idempotente: re-ejecutar un run no repite trabajo hecho | HU-013, HU-180 |

⇒ El catálogo debe: identificar cada asset de forma estable (HU-013/182), llevar dims y
flags (HU-018), y **admitir secciones nuevas sin romper lo anterior** (HU-035 añadirá
reportes de calidad; HU-019, etiquetas manuales).

## 3. La decisión de formato ya está tomada

Fuente: `docs/blueprint/adr/ADR-003-catalogo-local.md` (**Aceptado**):

> **Manifiestos JSON con claves ordenadas** como formato del catálogo local.
> - Serialización con `sort_keys=True`, `ensure_ascii=False`, UTF-8, indentado estable.
> - Las colecciones se ordenan por una clave explícita del dominio (hash o ruta) antes de
>   serializar: el orden es un dato, no un accidente de ejecución.
> - **Escritura atómica obligatoria (temporal + `rename`)** — requisito de HU-012, no opcional.
> - Un manifiesto por lote para el catálogo; sidecars por asset para el historial de
>   transformaciones (HU-057).

## 4. Restricciones del charter

Fuente: `docs/blueprint/charter.md` §6.1 y §6.3:

> 1. **Local y determinista** — misma entrada + mismo perfil ⇒ misma salida, byte a byte
>    donde el formato lo permita.
> 3. **No destructivo** — originales intactos; toda salida a **directorio de trabajo**.

## 5. Contratos del dominio ya disponibles

Verificado en `develop` (`f13f6eb`): `MediaAsset` (media_type, width, height,
content_hash, source, orientation derivada), `QualityReport`, `Transform`,
`TransformHistory`, y en `ingest/`: `TriageResult`/`QuarantinedAsset` con 6 causas,
`ExifData`, `ImageSize`, `DuplicateGroup`.

## 6. Reglas transversales aplicables

Fuente: `.claude/rules/python.md`:

> - Determinismo: semillas fijas, sin dependencia del orden del filesystem.
> - `pathlib.Path`, nunca `os.path`; contratos de dominio como dataclasses (frozen cuando aplique).
> - Seguridad: […] prohibidos `eval`/`exec`, `pickle.loads` sobre datos no confiables […]
> - Entradas hostiles se validan antes de procesar.

⇒ Al **leer** un catálogo hay que tratarlo como entrada no confiable: puede estar editado
a mano, truncado por un corte de luz o venir de otra versión del programa.

Cobertura exigida (CLAUDE.md Pre-Flight): ≥80% módulo tocado.

## 7. Alcance del ticket

Guardar y recuperar el catálogo de un lote sin poder corromperlo. La lógica de re-ingesta
idempotente es HU-013; el layout del directorio de trabajo, HU-016; el reporte legible,
HU-018.
