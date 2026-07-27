# HU-002 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E1 (commit `f10d05e`):

> | HU-002 | Validación de formatos de imagen soportados (**magic bytes, no extensión**) | Depende de: HU-001 | P0 | S |

Dependencia satisfecha: HU-001 **DONE** (`scan_input_folder` entrega rutas ordenadas).

## 2. Quiénes dependen de esta validación

Fuente: `docs/blueprint/backlog.md`, E1:

> | HU-004 | Lectura segura de EXIF: malformado o ausente degrada el asset, no tumba el lote | HU-002 |
> | HU-007 | Detección de compresión WhatsApp: techo 1288×952, peso, prefijo `WA` | HU-002 |
> | HU-009 | Archivos corruptos o truncados: **cuarentena con causa, pipeline sigue** | HU-002, HU-161 |
> | HU-011 | Límites de memoria y dimensiones: **rechazo de imágenes-bomba antes de decodificar** | HU-002 |

⇒ HU-002 es el punto donde se decide "esto es una imagen que sabemos procesar". HU-009
convierte los fallos en cuarentena con causa y HU-011 añade el límite de tamaño **antes**
de decodificar — esta HU debe dejar la puerta abierta a ese chequeo previo.

## 3. Formatos que el dominio produce

Fuente: `docs/blueprint/charter.md` §6.7:

> **Dispositivo de captura de referencia:** celular gama media (cliente 0: Redmi
> Note 13 Pro+). El pipeline asume medios de celular, no de cámara profesional.

Fuente: `docs/blueprint/insumos/documento-maestro.md` §8.1 (auditoría del archivo real):

> 🔴 HALLAZGO CRÍTICO — TODO EL ARCHIVO ESTÁ DEGRADADO POR WHATSAPP

⇒ El archivo real del cliente 0 son JPEG (celular + reenvío por WhatsApp). PNG y WebP son
plausibles (capturas de pantalla, descargas), HEIC es el formato nativo de iPhone.

## 4. Reglas transversales aplicables

Fuente: `.claude/rules/python.md`:

> - Entradas hostiles se validan **antes de procesar** (paths, formatos, tamaños, EXIF,
>   unicode, duplicados); un archivo corrupto **degrada ese asset, nunca tumba el pipeline**.
> - `pathlib.Path`, nunca `os.path`
> - Cero números mágicos — umbrales, pesos y rutas van a `config/` o al perfil de negocio.

Fuente: `docs/blueprint/adr/ADR-002-stack-vision.md` (Aceptado): OpenCV disponible para
decodificar; el ADR advierte que la superficie de import de cv2 vive fuera de `core/`.

Cobertura exigida (CLAUDE.md Pre-Flight): ≥80% módulo tocado.

## 5. Alcance del ticket

Determinar el formato real de un archivo **por su contenido** (firma binaria), no por la
extensión del nombre — un `.jpg` renombrado desde `.txt`, o un `.txt` que en realidad es
una foto, deben clasificarse por lo que son. La cuarentena (HU-009), el límite de tamaño
(HU-011) y el EXIF (HU-004) son HUs propias que consumen este veredicto.
