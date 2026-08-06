# HU-013 — Ticket de origen (extracto literal de fuentes canónicas)

## 1. La HU (backlog aprobado)

> | HU-013 | Re-ingesta idempotente: mismo input no duplica ni reprocesa | HU-012 | P0 | M |

Dependencia satisfecha: HU-012 **DONE** (catálogo con escritura atómica).

## 2. Consumidores

> | HU-019 | Sidecar de etiquetas manuales (ambiente, descarte, notas) que **sobrevive re-ingestas** | HU-013 | P1 | M |
> | HU-182 | Reanudación idempotente: re-ejecutar un run **no repite trabajo hecho** | HU-013, HU-180 | P1 | M |

⇒ Dos exigencias distintas: **no duplicar** (identidad estable) y **no reprocesar**
(saber qué ya se hizo). Y lo que el usuario haya anotado a mano debe sobrevivir.

## 3. Reglas aplicables

Fuente: `docs/blueprint/adr/ADR-004-acceso-al-filesystem.md` §Decisión 1:

> **El identificador de un asset es el hash de su contenido. El nombre y la ruta son
> metadatos, nunca identidad.** […] La re-ingesta idempotente (HU-013) compara por
> contenido, no por ruta.

Fuente: `docs/blueprint/adr/ADR-003-catalogo-local.md`:

> **Re-ingesta idempotente**: reejecutar sobre el mismo lote no debe duplicar ni reprocesar.
> […] mismo lote ⇒ archivo idéntico.

Fuente: `charter.md` §6.1: "misma entrada + mismo perfil ⇒ misma salida".

## 4. Escenarios reales que debe cubrir (del lote del cliente)

Medido el 26-jul sobre el archivo real: **109 archivos, 86 únicos por contenido, 15 grupos
de duplicados**. Es decir, la re-ingesta no es un caso hipotético: el propio lote ya trae
copias del mismo contenido con nombres distintos.

## 5. Alcance

Comparar un lote nuevo contra el catálogo existente y decir qué es nuevo, qué se mantiene,
qué desapareció y qué se movió de sitio. La orquestación de etapas es HU-180; el sidecar de
etiquetas, HU-019.
