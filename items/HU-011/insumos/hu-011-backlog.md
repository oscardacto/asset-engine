# HU-011 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E1 (commit `f10d05e`):

> | HU-011 | Límites de memoria y dimensiones: **rechazo de imágenes-bomba antes de
> decodificar** | Depende de: HU-002 | P0 | M |

Dependencias satisfechas: HU-002 **DONE** (formato por firma) · HU-009 **DONE** (registro
de cuarentena, diseñado para admitir causas nuevas).

## 2. Qué es una imagen-bomba

Un archivo pequeño que al decodificarse ocupa una cantidad desproporcionada de memoria:
un PNG de pocos KB puede declarar 60.000 × 60.000 píxeles y exigir ~10 GB al abrirse.
Por eso el ticket exige rechazarla **antes** de decodificar: cuando el proceso ya pidió la
memoria, es tarde.

HU-002 dejó el hueco a propósito. Fuente: `items/HU-002/spec/spec_tecnica.md` §5 RN-2:

> "rechazo de imágenes-bomba **antes de decodificar**" ⇒ La detección lee 16 bytes y nunca
> decodifica: HU-011 puede insertarse entre esta HU y la decodificación.

## 3. Quiénes más necesitan las dimensiones

Fuente: `docs/blueprint/backlog.md`:

> | HU-005 | Detección de orientación V/H (dimensiones + EXIF Orientation) | HU-004 |
> | HU-008 | Flag "bajo el nativo": resolución insuficiente por formato de salida del
> perfil (1080/1350/1920) | HU-007, HU-160 |
> | HU-018 | Reporte de inventario del lote (tabla por asset: **dims**, orientación, flags) |

⇒ Leer las dimensiones desde la cabecera no sirve solo para el límite: es una primitiva
que HU-005, HU-008 y HU-018 van a reutilizar sin pagar una decodificación.

## 4. El dispositivo de referencia condiciona el umbral

Fuente: `docs/blueprint/charter.md` §6.7:

> **Dispositivo de captura de referencia:** celular gama media (cliente 0: **Redmi
> Note 13 Pro+**). El pipeline asume medios de celular, no de cámara profesional.

⇒ Ese equipo tiene sensor de 200 MP. Una foto legítima suya son 200 millones de píxeles
(~600 MB ya decodificada): cualquier umbral pensado para "fotos normales" la rechazaría.

## 5. Reglas transversales aplicables

Fuente: `.claude/rules/python.md`:

> - Entradas hostiles se validan **antes de procesar** (paths, formatos, **tamaños**, EXIF…)
> - **Cero números mágicos** — umbrales, pesos y rutas van a `config/` o al perfil de negocio.
> - un archivo corrupto degrada ese asset, nunca tumba el pipeline.

⇒ `config/` aún no existe (HU-155): el umbral vive como constante nombrada del módulo,
documentada como promovible, igual que se hizo con el bloque de lectura en HU-006.

Cobertura exigida (CLAUDE.md Pre-Flight): ≥80% módulo tocado.

## 6. Alcance del ticket

Obtener las dimensiones declaradas en la cabecera de cada formato soportado, sin
decodificar, y apartar los archivos cuya decodificación pediría memoria desproporcionada.
El presupuesto de rendimiento por etapa es HU-165; el flag "bajo el nativo" es HU-008.
