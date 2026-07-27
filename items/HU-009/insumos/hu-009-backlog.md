# HU-009 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E1 (commit `f10d05e`):

> | HU-009 | Archivos corruptos o truncados: **cuarentena con causa, pipeline sigue** | Depende de: HU-002, HU-161 | P0 | M |

Dependencias satisfechas: HU-002 **DONE** (detección de formato por firma) y HU-161
**DONE** (`CorruptMediaError` con `source` + `reason`).

## 2. La tensión central del ticket

Fuente: `docs/blueprint/charter.md` §6.3:

> **No destructivo** — originales intactos; toda salida a directorio de trabajo con
> historial de transformaciones.

Fuente: `.claude/rules/python.md`:

> un archivo corrupto **degrada ese asset, nunca tumba el pipeline**.

⇒ "Cuarentena" no puede significar mover el archivo del usuario a otra carpeta: eso
tocaría el original. Tampoco copiarlo (duplicaría gigabytes de video sin aportar nada).
La cuarentena es un **registro** de qué se apartó y por qué.

## 3. Quiénes consumen el resultado

Fuente: `docs/blueprint/backlog.md`:

> | HU-016 | Directorio de trabajo no destructivo: layout de salidas + verificación de que
> el origen queda intacto | HU-012 |
> | HU-018 | Reporte de inventario del lote (tabla por asset: dims, orientación, flags —
> formato Maestro §8.2) | HU-017 |
> | HU-180 | Orquestador de etapas: un asset que falla degrada, el lote continúa;
> **resumen de fallos** | HU-161, HU-168 |
> | HU-011 | Límites de memoria y dimensiones: rechazo de imágenes-bomba **antes de
> decodificar** | HU-002 |

⇒ El registro de cuarentena alimenta el resumen de fallos (HU-180) y el reporte de
inventario (HU-018). HU-011 añadirá una causa más (imagen-bomba) al mismo mecanismo.

## 4. Qué causas existen ya en el código

Verificado en `develop` (`a0a89a6`): `detect_image_format` devuelve `None` (firma
desconocida), un `ImageFormat` no soportado (HEIC/AVIF) o lanza `CorruptMediaError`
(ilegible). El generador de fixtures (HU-166) produce además JPEG **truncados** y
archivos vacíos.

## 5. Reglas transversales aplicables

Fuente: `.claude/rules/python.md`:

> - Entradas hostiles se validan antes de procesar […]
> - Manejo de errores explícito · Determinismo: sin dependencia del orden del filesystem.
> - Cero números mágicos.

Cobertura exigida (CLAUDE.md Pre-Flight): ≥80% módulo tocado.

## 6. Alcance del ticket

Clasificar cada archivo escaneado en **utilizable** o **apartado con causa**, sin tocar
los originales y sin detener el lote. La decodificación real, el límite de tamaño
(HU-011) y la escritura del reporte a disco (HU-016/018) son HUs propias.
