# HU-010 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E1 (commit `f10d05e`):

> | HU-010 | Paths unicode, nombres hostiles y colisiones de nombre | Depende de: HU-001 | P0 | S |

> **El título describe una hipótesis, no un diagnóstico.** La evidencia empírica recogida
> antes de especificar la refutó: ver `evidencia-empirica.md` y §13 de la spec.

## 2. Lo que HU-001 dejó explícitamente pendiente

Fuente: `items/HU-001/spec/spec_tecnica.md` §2.2 (OUT):

> Hash y duplicados → HU-006 · **Normalización de nombres hostiles y colisiones → HU-010**.

Fuente: `items/HU-001/closure/feedback.md`:

> "La clave necesitó tres componentes: forma Unicode fija (NFC), insensibilidad a mayúsculas
> […] y la ruta cruda como último desempate, porque dos nombres distintos pueden normalizar
> al mismo NFC y NTFS los deja coexistir."

⇒ HU-001 resolvió el **orden**. La **accesibilidad** de esas rutas quedó sin resolver.

## 3. Reglas que la HU debe hacer cumplir

Fuente: `.claude/rules/python.md`:

> - Entradas hostiles se validan antes de procesar (paths, formatos, tamaños, EXIF,
>   **unicode, duplicados**); un archivo corrupto **degrada ese asset, nunca tumba el
>   pipeline**.
> - `pathlib.Path`, nunca `os.path`
> - Composición sobre herencia; fail fast en violaciones de contrato, **fail safe en datos
>   del usuario**.

Fuente: `.claude/CLAUDE.md` (Checklist Pre-Flight):

> □ Manejo de errores explícito: un archivo corrupto degrada esa foto, no tumba el pipeline
> □ Validación de entradas hostiles antes de procesar (paths, formatos, tamaños, EXIF)

Fuente: `docs/blueprint/charter.md` §6.3:

> **No destructivo** — originales intactos.

## 4. Consumidores y vecinos relevantes

Fuente: `docs/blueprint/backlog.md`:

> | HU-016 | Directorio de trabajo no destructivo: layout de salidas + verificación de que
> el origen queda intacto | HU-012 | P0 | S |
> | HU-012 | Persistencia del catálogo (según ADR HU-153) con escritura atómica | HU-153, HU-157 |
> | HU-180 | Orquestador de etapas: **un asset que falla degrada, el lote continúa**;
> resumen de fallos | HU-161, HU-168 |

## 5. Alcance del ticket

Que ningún archivo de la carpeta de entrada pueda bloquear, detener ni hacer desaparecer
material del pipeline. El saneamiento de nombres **al escribir salidas** es HU-016; la
validación de la cadena de video con rutas extendidas es HU-154.
