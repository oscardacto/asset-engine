# Spec Técnica `HU-051` (+052+055) — `Motor de transformaciones + primera tanda`

> **Estado:** LISTA PARA DEV · **Fecha:** 2026-08-06 · **Confianza:** 90%

## 1. El contrato común del Develop Pipeline

Toda transformación presente y futura cumple **el mismo contrato**, y agregar una nueva
jamás toca el motor:

| Aspecto | Contrato |
|---------|----------|
| **Entrada** | `Image` (ndarray BGR uint8) — nunca se muta: se devuelve una nueva |
| **Salida** | `Image` de iguales garantías (dtype/canales), dims iguales salvo transforms geométricos |
| **Configuración** | `Mapping[str, ParamValue]` — **datos del perfil** (HU-056/HU-135); el motor no conoce valores |
| **Parámetros** | Cada transform valida los suyos al construir el plan; desconocidos o fuera de rango ⇒ `InvalidInputError` (dato del usuario) **antes** de tocar ninguna foto |
| **Metadata / trazabilidad** | Cada aplicación produce el `Transform(name, params)` de HU-159; el pipeline devuelve el `TransformHistory` completo — la evidencia auditable |
| **Métricas / tiempos** | Del `StageReport` de la etapa (HU-168); el motor no mide por transform hasta que HU-165 lo pida con presupuesto |
| **Errores** | Fallo aplicando sobre una foto ⇒ `CorruptMediaError` de esa foto: degrada, no tumba |
| **Determinismo** | Funciones puras sin aleatoriedad; misma imagen + mismos params ⇒ mismos bytes |
| **Registro** | `TRANSFORMS: dict[str, TransformSpec]` — igual que etapas y reportes: **agregar = registrar**, el motor y la CLI no cambian |

`TransformSpec = (apply: (Image, params) -> Image, validate: (params) -> None)`.

## 2. Primera tanda (esta HU)
- `clahe` (HU-051): clip_limit + tile_size, sobre el canal L de LAB — contraste local sin reventar color.
- `white_balance` (HU-052): calidez solo en luces (referencia revelado 25-jul): gain de temperatura ponderado por luminancia.
- `saturation` (HU-055): factor con tope del perfil (cliente 0 ≤ +6%).

## CA
- CA-1 Contrato: registrar un transform nuevo no toca `apply_pipeline` (test que registra uno falso).
- CA-2 Params inválidos fallan al armar el plan, antes de procesar.
- CA-3 Cada transform es determinista y no muta la entrada.
- CA-4 CLAHE sube contraste local; WB calienta luces más que sombras; saturation respeta tope.
- CA-5 El historial devuelto es la secuencia exacta aplicada.
- CA-6 Cobertura ≥80% · gobernanza verde · gate-log 051/052/055.
