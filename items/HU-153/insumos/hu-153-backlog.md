# HU-153 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E7 (commit `f10d05e`):

> | HU-153 | `ADR` Catálogo local: manifiestos JSON vs SQLite | Depende de: HU-150 | P0 | S |

Fuente: `.claude/CLAUDE.md` (Stack tecnológico):

> | Catálogo local | Manifiestos JSON vs SQLite (**ADR pendiente**) |

Es el **último ADR de stack sin cerrar**. HU-151 (uv) y HU-152 (OpenCV) están Aceptados.

## 2. Quiénes dependen de la decisión

Fuente: `docs/blueprint/backlog.md`:

> | HU-012 | Persistencia del catálogo (según ADR HU-153) con **escritura atómica** | HU-153, HU-157 |
> | HU-013 | **Re-ingesta idempotente: mismo input no duplica ni reprocesa** | HU-012 |
> | HU-018 | Reporte de inventario del lote (tabla por asset: dims, orientación, flags) | HU-017 |
> | HU-035 | `QualityReport` agregado y serializado al catálogo |
> | HU-057 | Historial de transformaciones por asset (**sidecar auditable**) |

## 3. Restricciones del charter que condicionan la decisión

Fuente: `docs/blueprint/charter.md` §6.1 y §7:

> 1. **Local y determinista** — sin nube, sin APIs remotas; misma entrada + mismo perfil
>    ⇒ misma salida, **byte a byte donde el formato lo permita**.

> | Reproducibilidad | 100% — misma entrada+perfil ⇒ misma salida (**verificado en CI con
> golden tests**) |

Fuente: `docs/blueprint/charter.md` §2 (Visión):

> devuelve un directorio de trabajo con: análisis técnico por asset […] y reporte de
> cobertura de ambientes

Fuente: `.claude/CLAUDE.md` (Esquema de Datos):

> No hay base de datos externa. El catálogo de medios es local (manifiestos JSON o SQLite
> — ADR pendiente) y **siempre cabe consultarlo con las herramientas del repo**.

## 4. Escala real del problema

Fuente: `docs/blueprint/insumos/documento-maestro.md` §8.2: la auditoría del cliente 0
cubre **43 fotos**. El backlog no contempla lotes de decenas de miles: el caso de uso es
una sesión de fotos de un hospedaje, no un archivo fotográfico corporativo.

## 5. Reglas transversales aplicables

Fuente: `.claude/rules/python.md`:

> - Seguridad: prohibidos `eval`/`exec`, `pickle.loads` sobre datos no confiables,
>   `yaml.load` sin `SafeLoader` […]

⇒ Descarta de entrada formatos de serialización que ejecuten código (pickle) o que
requieran cargador seguro explícito (YAML).

## 6. Alcance del ticket

Cerrar la decisión con un ADR. La implementación de la persistencia (escritura atómica,
esquema concreto de los campos) es **HU-012**, que consume esta decisión.
