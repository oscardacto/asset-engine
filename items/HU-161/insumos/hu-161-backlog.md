# HU-161 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E7 (commit `f10d05e`):

> | HU-161 | Jerarquía de excepciones del dominio (corrupto ≠ inválido ≠ bug) | Depende de: HU-150 | P0 | S |

Dependencia satisfecha: HU-150 **DONE**.

## 2. Quiénes lanzan y quiénes capturan (semántica de las 3 categorías)

Fuente: `docs/blueprint/backlog.md`:

**Corrupto** — el archivo no se puede leer/decodificar; se aísla y el lote sigue:

> | HU-009 | Archivos corruptos o truncados: **cuarentena con causa, pipeline sigue** |
> | HU-004 | Lectura segura de EXIF: malformado o ausente **degrada el asset, no tumba el lote** |

**Inválido** — la entrada se lee pero no sirve; el usuario recibe un mensaje accionable:

> | HU-002 | Validación de formatos de imagen soportados (magic bytes, no extensión) |
> | HU-136 | Perfil hostil o incompleto: **mensajes de error accionables, nunca stacktrace** |
> | HU-011 | Límites de memoria y dimensiones: **rechazo de imágenes-bomba antes de decodificar** |

**El orquestador es el consumidor central de la distinción:**

> | HU-180 | Orquestador de etapas: **un asset que falla degrada, el lote continúa**; resumen de fallos |

## 3. Reglas transversales aplicables

Fuente: `.claude/rules/python.md`:

> - Composición sobre herencia; **fail fast en violaciones de contrato, fail safe en datos del usuario.**
> - Entradas hostiles se validan antes de procesar (paths, formatos, tamaños, EXIF, unicode,
>   duplicados); un archivo corrupto degrada ese asset, nunca tumba el pipeline.

Fuente: `.claude/CLAUDE.md` (Checklist Pre-Flight):

> □ Manejo de errores explícito: un archivo corrupto degrada esa foto, no tumba el pipeline

Precedente ya sembrado en `core/` (HU-157/158): las violaciones de contrato de las
dataclasses lanzan `ValueError` — es decir, **"bug" ya tiene representación: excepciones
estándar de Python que nadie del dominio captura**.

## 4. Alcance del ticket

Definir las categorías del dominio (corrupto, inválido) como jerarquía de excepciones en
`core/`, dejando explícito que "bug" queda FUERA de la jerarquía (excepciones estándar,
revientan). El uso real (cuarentena, mensajes CLI, orquestación) es de HU-009/136/180.
