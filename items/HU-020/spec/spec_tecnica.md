# Spec Técnica `HU-020` (+021+022) — `Métricas de exposición`

> **Estado:** LISTA PARA DEV
> **Fecha:** 2026-08-06
> **Confianza global:** 90%

## 1. Resumen ejecutivo
- **Qué se pide:** las tres métricas base de exposición por foto — brillo medio, % de
  píxeles en negro aplastado y % de altas luces quemadas.
- **Módulo:** `media_optimizer.vision.exposure` — primer módulo de `vision/`, las
  primitivas compartidas de visión.
- **No obvio — qué es "brillo" tiene una respuesta correcta y varias incorrectas.** La
  auditoría del cliente se hizo a ojo sobre las fotos como se ven, así que la métrica debe
  medir **luminancia perceptual** (Rec. 601: 0.299R + 0.587G + 0.114B), no el promedio de
  los tres canales. Sobre una foto muy cálida (los interiores del cliente) ambas difieren
  varios puntos — suficiente para romper la paridad ±2% del KPI. OpenCV además entrega BGR,
  no RGB: usar los coeficientes en el orden equivocado sesga el resultado hacia el azul.

## 2. Alcance
### 2.1 IN
- `luminance(image)`: el mapa de luminancia perceptual de una imagen BGR.
- `mean_brightness(image)`: brillo medio [0, 255].
- `crushed_shadows_ratio(image, threshold)`: fracción de píxeles bajo el umbral.
- `blown_highlights_ratio(image, threshold)`: fracción de píxeles sobre el umbral.
- `decode_image(path)`: decodifica vía la capa de ADR-004 (cv2.imdecode sobre bytes ya
  leídos — **nunca** cv2.imread sobre la ruta, que se salta la capa y muere con rutas
  hostiles).
### 2.2 OUT
- Umbrales concretos → datos del perfil (HU-133); aquí son parámetros.
- Score compuesto y veredicto → HU-029/030.
- Conexión con la etapa `analyze` → HU-037.
- Nitidez, ruido, color → sus HUs.

### 2.3 Casos límite
| # | Caso | Tratamiento |
|---|------|-------------|
| 1 | Imagen totalmente negra / blanca | ratios 1.0 y 0.0 exactos |
| 2 | Imagen en escala de grises (1 canal) | La luminancia es el canal tal cual |
| 3 | Archivo que el triaje aceptó pero cv2 no decodifica | `CorruptMediaError` con la ruta |
| 4 | Umbral fuera de [0, 255] | `ValueError`: contrato roto, no dato del usuario |

## 5. Reglas de negocio
| # | Regla | Implicación |
|---|-------|-------------|
| RN-1 | Paridad ±2% con la auditoría manual (charter §7) | Luminancia perceptual, no promedio de canales; test con fixtures de brillo conocido |
| RN-2 | Umbrales del perfil (charter §3) | Parámetros, jamás constantes |
| RN-3 | Todo IO por la capa (ADR-004) | `decode_image` lee bytes por `filesystem` y decodifica en memoria |
| RN-4 | Determinismo (charter §6.1) | Aritmética entera/float64 sin aleatoriedad |
| RN-5 | Corrupto degrada (charter) | `CorruptMediaError`, no crash |

## 8. Riesgos
| # | Riesgo | Mitigación |
|---|--------|------------|
| R-1 | Promedio de canales en vez de luminancia rompe el KPI | Test con imagen de color puro donde ambas difieren mucho |
| R-2 | Orden BGR/RGB invertido | Test asimétrico: rojo puro debe dar ≈76, azul puro ≈29 |
| R-3 | `cv2.imread` directo se cuele | Ya prohibido por el test de arquitectura |

## 9. Confianza global
0 bloqueantes · coeficientes Rec.601 verificables por test · **90%** ✅

## 11. Criterios de aceptación
- **CA-1** — `mean_brightness` sobre un fixture de brillo B conocido da B ±2 (el KPI).
- **CA-2** — Rojo puro ≈ 76 y azul puro ≈ 29: luminancia perceptual con orden BGR correcto.
- **CA-3** — `crushed_shadows_ratio` y `blown_highlights_ratio` exactos sobre imágenes sintéticas con proporciones conocidas.
- **CA-4** — Imagen negra: crushed=1.0, blown=0.0; blanca: al revés.
- **CA-5** — Los umbrales son parámetros; ninguno vive como constante del módulo.
- **CA-6** — `decode_image` pasa por la capa: funciona en ruta larga; corrupto ⇒ `CorruptMediaError`.
- **CA-7** — Determinismo: misma imagen ⇒ mismos valores exactos, dos veces.
- **CA-8** — Gobernanza verde · cobertura ≥80% · gate-log (evento por HU: 020, 021, 022).
