# HU-004 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E1 (commit `f10d05e`):

> | HU-004 | Lectura segura de EXIF: **malformado o ausente degrada el asset, no tumba el
> lote** | Depende de: HU-002 | P0 | M |

Dependencias satisfechas: HU-002 **DONE** · HU-009/HU-011 **DONE** (registro de cuarentena
y lectura de cabeceras ya operativos).

## 2. Quiénes consumen el EXIF

Fuente: `docs/blueprint/backlog.md`:

> | HU-005 | Detección de orientación V/H (**dimensiones + EXIF Orientation**) | HU-004 |
> | HU-015 | Agrupación por sesión de captura (huecos temporales configurables) | HU-012 |
> | HU-018 | Reporte de inventario del lote (tabla por asset: dims, orientación, flags) | HU-017 |

Fuente: `docs/blueprint/insumos/documento-maestro.md` §8.2: la auditoría manual del cliente
registró **orientación** por foto; la serie del 4 de abril son "verticales luminosas".

## 3. Hallazgo que condiciona el diseño (verificado antes de especificar)

Ejecutado sobre el stack real (opencv-python-headless 5.0.0.93):

| Comprobación | Resultado |
|---|---|
| `cv2.imreadWithMetadata` / `imdecodeWithMetadata` / `imencodeWithMetadata` | **existen en OpenCV 5** |
| Ida y vuelta de EXIF (escribir + volver a leer) | ✅ byte a byte idéntico |
| Archivo sin EXIF | devuelve lista de tipos vacía, sin excepción |
| Imagen 48×96 con `Orientation=1` → `imdecode` | (48, 96) — sin cambio |
| Imagen 48×96 con `Orientation=6` → `imdecode` | **(96, 48) — OpenCV la rota** |
| La misma con `IMREAD_IGNORE_ORIENTATION` | (48, 96) — cruda |

⇒ Dos consecuencias: (1) **no hace falta dependencia nueva** para leer ni escribir EXIF, lo
que **invalida la asunción A-2 de HU-166** ("cv2 no escribe EXIF; hará falta una dependencia
con su ADR"); (2) la orientación EXIF **no es un dato pasivo**: OpenCV la aplica al
decodificar, así que las dimensiones de cabecera y las decodificadas pueden discrepar.

## 4. Reglas transversales aplicables

Fuente: `.claude/rules/python.md`:

> - Entradas hostiles se validan antes de procesar (paths, formatos, tamaños, **EXIF**,
>   unicode, duplicados); un archivo corrupto **degrada ese asset, nunca tumba el pipeline**.
> - Determinismo: sin dependencia del orden del filesystem.

Fuente: `docs/blueprint/charter.md` §6.6: los medios del cliente pueden contener PII; todo
procesamiento es local. El EXIF puede incluir **GPS** — dato sensible.

Cobertura exigida (CLAUDE.md Pre-Flight): ≥80% módulo tocado.

## 5. Alcance del ticket

Leer el EXIF sin que un bloque malformado detenga el lote. La decisión de orientación V/H
es HU-005; la agrupación por sesión, HU-015; el flag de PII, HU-034.
