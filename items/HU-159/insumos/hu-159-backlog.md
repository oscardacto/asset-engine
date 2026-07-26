# HU-159 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E7 (commit `f10d05e`):

> | HU-159 | Contrato `Transform` + historial de transformaciones aplicadas | Depende de: HU-157 | P0 | S |

Dependencia satisfecha: HU-157 **DONE**.

## 2. Quiénes producen y consumen transforms

Fuente: `docs/blueprint/backlog.md`, E3 (revelado) — cada etapa del revelado ES un transform:

> | HU-050 | Corrección de perspectiva/verticales (a partir del ángulo de HU-028) | HU-028, **HU-159** |
> | HU-051 | CLAHE parametrizado por perfil (clip limit, tiles) | **HU-159** |
> | HU-052 | White balance con calidez solo en luces (referencia: revelado 25-jul) | HU-026, **HU-159** |
> | HU-053 | Recuperación de sombras con máscara ponderada por luminancia | HU-021, **HU-159** |
> | HU-056 | Pipeline de revelado componible: **orden y parámetros de transforms declarados en el perfil** |
> | HU-057 | **Historial de transformaciones por asset (sidecar auditable)** |

Observabilidad y no-destructividad — el historial es dato de primera clase:

> | HU-168 | Contrato `StageReport`: tiempo, memoria pico, **transformaciones**, scores por etapa |

Fuente: `docs/blueprint/charter.md` §6.3:

> **No destructivo** — originales intactos; toda salida a directorio de trabajo **con
> historial de transformaciones**.

## 3. Reglas transversales aplicables

Fuente: `.claude/rules/python.md`:

> - Cero números mágicos — umbrales, pesos y rutas van a `config/` o al perfil de negocio.
> - contratos de dominio como dataclasses (frozen cuando aplique).
> - Determinismo: semillas fijas, sin dependencia del orden del filesystem.

Implicación directa de HU-056: **los parámetros de un transform son datos del perfil**
(clip limit, tiles, targets) — el contrato transporta nombre + parámetros, no lógica.

Precedentes en `core/` (HU-157/158): frozen+slots, igualdad por valor, colecciones
congeladas con copia defensiva, NaN/±inf rechazados en floats, ValueError = bug.

## 4. Alcance del ticket (los 2 conceptos, literales)

`Transform` (qué operación con qué parámetros) + `historial de transformaciones
aplicadas` (secuencia ordenada, auditable). La ejecución real de cada transform es de
E3; la serialización del sidecar es de HU-057; el reporte por etapa es de HU-168.
