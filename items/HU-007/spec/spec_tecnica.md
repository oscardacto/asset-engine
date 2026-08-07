# Spec Técnica `HU-007` (+008) — `Flags de degradación`

> **Estado:** LISTA PARA DEV
> **Fecha:** 2026-08-06
> **Confianza global:** 89%

## 1. Resumen ejecutivo
- **Qué se pide:** los dos flags de material degradado: `whatsapp_compressed` (la foto pasó
  por la compresión de WhatsApp) y `below_native` (no alcanza para algún formato de salida
  del perfil).
- **Módulo:** `media_optimizer.ingest.degradation` — flags que se derivan de metadatos ya
  medidos en la ingesta, sin decodificar la imagen.
- **No obvio — la señal del enunciado se midió y quedó obsoleta.** El techo 1288×952 habría
  dado 16/16 falsos negativos: WhatsApp hoy reenvía en HD. La regla calibrada sobre el lote
  real es **nombre WA** (suficiente) **o EXIF ausente ∧ < 0.15 bytes/píxel** — separa 16/16
  con 0 FP. El alcance de la HU (detectar compresión WhatsApp, KPI 0 FP) no cambia; cambia
  la señal, que el propio enunciado listaba como hipótesis.

## 2. Alcance
### 2.1 IN
- `whatsapp_compression(name, size_bytes, pixels, exif_present, *, max_bytes_per_pixel)`.
- `below_native(width, height, formats)` → intenciones del perfil que la foto no alcanza
  (reutiliza `OutputFormat.accepts` de HU-160).
- El umbral de bytes/píxel es **parámetro**; el valor calibrado (0.15) queda documentado y
  lo pasará el perfil (HU-133) — hasta entonces, quien invoque usa la constante calibrada
  exportada como dato con nombre.
### 2.2 OUT
- Escribir los flags al catálogo/QualityReport → HU-035/037.
- La serie completa de 43 WA → se re-valida al llegar (insumo pendiente).

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Foto WA renombrada | La señal física (EXIF+bpp) la atrapa igual |
| 2 | Editada de agencia sin EXIF | bpp ≥0.234 medido: no dispara |
| 3 | Foto con 0 píxeles declarados | Contrato roto: `ValueError` |
| 4 | Perfil sin formatos | `below_native` devuelve vacío: nada que incumplir |

## 5. Reglas de negocio
| RN | Regla | Implicación |
|----|-------|-------------|
| RN-1 | KPI: detección 100%, 0 FP (charter §7) | Validación contra el lote real completo en el cierre |
| RN-2 | Umbrales como datos (charter §3) | Parámetro + constante calibrada con nombre |
| RN-3 | Sin IO | Recibe metadatos ya medidos; no abre archivos |

## 9. Confianza global
0 bloqueantes · regla calibrada empíricamente sobre 102 assets · **89%** ✅

## 11. Criterios de aceptación
- **CA-1** — El patrón de nombre WA dispara el flag por sí solo.
- **CA-2** — EXIF ausente + bpp bajo dispara el flag aunque el nombre no ayude.
- **CA-3** — Las editadas sin EXIF pero pesadas **no** disparan (el caso FP real).
- **CA-4** — Sobre el lote real: **16/16 WA detectadas, 0 FP en 86 no-WA**.
- **CA-5** — `below_native` devuelve exactamente las intenciones que la foto no alcanza.
- **CA-6** — Una foto que alcanza todo devuelve vacío; perfil sin formatos, vacío.
- **CA-7** — Umbral como parámetro; cero números sin nombre.
- **CA-8** — Gobernanza + cobertura ≥80% + gate-log (007 y 008).
