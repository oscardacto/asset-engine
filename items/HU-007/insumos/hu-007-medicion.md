# Insumo — HU-007 (+008): medición previa sobre el lote real (2026-08-06)

| ID | HU | Prio |
|----|----|------|
| HU-007 | Detección de compresión WhatsApp: techo 1288×952, peso, prefijo `WA` (KPI: 43/43 del cliente 0, 0 FP en serie 4-abr) | P0 |
| HU-008 | Flag "bajo el nativo": resolución insuficiente por formato de salida del perfil | P0 |

## La hipótesis del enunciado quedó obsoleta, y se midió

El enunciado propone el **techo 1288×952** como señal. Medido sobre las 16 fotos WA del
lote real: **todas son 4080×3060** — WhatsApp hoy reenvía en HD y el techo ya no existe.
Esa señal habría producido **16 falsos negativos de 16**.

## Lo que sí discrimina, medido sobre los 102 assets

| Población | bytes/píxel | EXIF presente |
|-----------|-------------|---------------|
| WA (16) | 0.022 – **0.114** | **0/16** |
| no-WA (86) | 0.078 – 0.396 | 83/86 |
| no-WA **sin** EXIF (3, editadas de agencia) | **0.234** – 0.396 | — |

**Regla calibrada: EXIF ausente ∧ bytes/píxel < 0.15** → separa 16/16 con 0 FP: los no-WA
o conservan EXIF o pesan ≥0.234 B/px. El nombre `IMG-\d{8}-WA\d+` es señal suficiente
adicional (WhatsApp lo pone; una foto renombrada pierde esa señal pero conserva la física).

## KPI 43/43
La serie de 43 fotos WA del cliente 0 aún no está en el lote entregado (hay 16). El KPI se
valida 16/16 + 0 FP sobre lo disponible; la serie completa se re-valida cuando llegue
(insumo pendiente ya registrado).
