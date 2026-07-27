# HU-006 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E1 (commit `f10d05e`):

> | HU-006 | Hash de contenido y detección de duplicados exactos | Depende de: HU-001 | P0 | S |

Dependencia satisfecha: HU-001 **DONE** (`scan_input_folder` entrega rutas ordenadas).

## 2. Quiénes consumen el hash

Fuente: `docs/blueprint/backlog.md`:

> | HU-012 | Persistencia del catálogo (según ADR HU-153) con escritura atómica | HU-153, HU-157 |
> | HU-013 | **Re-ingesta idempotente: mismo input no duplica ni reprocesa** | HU-012 |
> | HU-075 | Detección de **near-duplicates** para diversidad de la selección | HU-006, HU-070 |

Fuente: `.claude/CLAUDE.md` (contratos): `MediaAsset` incluye `content_hash` — el hash es
el identificador de contenido del asset en todo el pipeline.

⇒ Dos usos distintos: **identidad** (clave estable del asset para el catálogo y la
re-ingesta idempotente) y **duplicados exactos** (mismo contenido con distinto nombre).
Los near-duplicates perceptuales son HU-075, otra técnica.

## 3. Por qué importa en el archivo real del cliente 0

Fuente: `docs/blueprint/insumos/documento-maestro.md` §8.1:

> 🔴 HALLAZGO CRÍTICO — TODO EL ARCHIVO ESTÁ DEGRADADO POR WHATSAPP

⇒ Un archivo reenviado por WhatsApp y guardado varias veces produce copias idénticas con
nombres distintos (`IMG-20250404-WA0012.jpg`, `IMG-20250404-WA0012 (1).jpg`). Detectarlas
evita analizar y revelar el mismo material dos veces.

## 4. Reglas transversales aplicables

Fuente: `.claude/rules/python.md`:

> - Determinismo: semillas fijas, **sin dependencia del orden del filesystem**.
> - Sin estado global; **video siempre en streaming (nunca cargar el video completo a RAM)**;
>   evitar copias innecesarias de arrays NumPy.
> - Entradas hostiles se validan antes de procesar […] un archivo corrupto degrada ese
>   asset, nunca tumba el pipeline.
> - Seguridad: prohibidos `eval`/`exec`, `pickle.loads` sobre datos no confiables […]

⇒ El hash se calcula **por bloques** (streaming), no cargando el archivo entero: un video
de 2 GB no puede entrar a RAM. Y el agrupamiento de duplicados debe ser determinista, sin
depender del orden en que llegaron los archivos.

Cobertura exigida (CLAUDE.md Pre-Flight): ≥80% módulo tocado.

## 5. Alcance del ticket

Calcular una huella estable del **contenido** de cada archivo y agrupar los que la
comparten. La política de qué hacer con los duplicados (cuál conservar, si se descartan o
solo se marcan) pertenece a la ingesta/catálogo (HU-012/013) y al reporte (HU-018).
