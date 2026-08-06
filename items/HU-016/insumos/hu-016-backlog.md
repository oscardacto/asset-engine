# HU-016 — Ticket de origen (extracto literal)

## 1. La HU

> | HU-016 | Directorio de trabajo no destructivo: layout de salidas + verificación de que el
> origen queda intacto + **saneamiento de nombres al escribir, vía la capa de ADR-004** |
> HU-012, HU-010 | P0 | S |

> La cláusula en negrita se añadió al backlog al cerrar HU-010, por decisión del equipo.

Dependencias satisfechas: HU-012 **DONE** (catálogo), HU-010 **DONE** (capa de acceso).

## 2. Quiénes escribirán en este directorio

> | HU-057 | Historial de transformaciones por asset (sidecar auditable) | HU-056 |
> | HU-061 | Export JPEG: calidad configurable, metadatos limpios (sin GPS/PII) | HU-060 |
> | HU-036 | Reporte comparativo del lote | HU-035 |
> | HU-181 | Reporte consolidado del run en Markdown | HU-036, HU-076 |

## 3. La regla que la HU hace cumplir

Fuente: `charter.md` §6.3:

> **No destructivo** — originales intactos; toda salida a **directorio de trabajo** con
> historial de transformaciones.

Fuente: `docs/blueprint/adr/ADR-004-acceso-al-filesystem.md` §Decisión 4, corolario:

> al **escribir** en el directorio de trabajo (HU-016), el nombre sí se normaliza, porque la
> ruta extendida permite crear nombres que después son inaccesibles por vías normales.
> Adaptar la ruta y sanear el nombre son problemas distintos: el primero es de lectura, el
> segundo de escritura.

## 4. Evidencia sobre colisiones (medida en HU-010)

En NTFS, `Foto.jpg` y `foto.jpg` **no coexisten**: el segundo sobrescribe al primero en
silencio. Dos assets de entrada distintos pueden pisarse en la salida sin dejar traza.

## 5. Alcance

Definir dónde van las salidas, garantizar que el origen no se toca, y convertir cualquier
nombre de entrada en un nombre de salida escribible y sin colisiones. El contenido de cada
salida es de su propia HU.
