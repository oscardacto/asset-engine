# HU-005 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E1:

> | HU-005 | Detección de orientación V/H (dimensiones + EXIF Orientation) | HU-004 | P0 | S |

Dependencia satisfecha: HU-004 **DONE** (`ExifOrientation`, `oriented_size`).

## 2. Consumidores — todos implícitos, ninguno la declara en su columna

Hallazgo de la investigación: **ninguna HU declara HU-005 en "Depende de"**. Los
consumidores aparecen por texto:

> | HU-018 | Reporte de inventario del lote (tabla por asset: dims, **orientación**, flags — formato Maestro §8.2) | HU-017 |
> | HU-059 | Salida 9:16 para stories **desde verticales** (crop o extensión según perfil) | HU-056 |
> | HU-074 | Selección por formato de salida: portada / feed 4:5 / story 9:16, con elegibilidad técnica | HU-070, HU-008 |

## 3. La tensión de diseño (verificada en el código y en HU-004)

- `core.Orientation` (HU-157) se deriva **solo de las dimensiones**, sin EXIF, por la regla
  de dominio puro.
- HU-004 midió que **OpenCV gira la imagen al decodificar** si el EXIF lo indica: una foto
  de 48×96 con `Orientation=6` vuelve como 96×48.
- Consecuencia: la misma foto es "vertical" leída de cabecera y "horizontal" ya abierta.

Fuente: `items/HU-004/spec/spec_tecnica.md` §8 R-2:

> "Discrepancia silenciosa entre dimensiones de cabecera y decodificadas […] `oriented_size`
> explícito + documentación del comportamiento; **HU-005 decidirá cuál usa y por qué**."

## 4. Qué auditó el cliente

Fuente: `docs/blueprint/insumos/documento-maestro.md` §8.2 — la orientación es columna por
foto, anotada **a ojo** sobre la imagen ya vista. Sobre la serie del 4 de abril:

> "Cinco de estas siete son verticales y luminosas — la combinación exacta que faltaba para
> Reels, TikTok y Stories, y que se dio por inexistente."

⇒ La orientación que importa al negocio es la **visible**, no la cruda.

## 5. Datos del lote real (medidos el 26-jul sobre el archivo del cliente)

Orientación por dimensiones crudas: **V=76 · H=20 · cuadradas=4**.
Fotos con `Orientation` EXIF declarada: **10, todas con valor 1** (sin giro).

⇒ En este lote concreto cruda y visible coinciden. Pero el pipeline no puede depender de eso.

## 6. Alcance del ticket

Decidir y exponer la orientación **efectiva** de un asset. El reporte es HU-018; la
elegibilidad por formato de salida, HU-074.
