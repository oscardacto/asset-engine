# Spec Técnica `HU-053` (+054+058+060) — `Tanda 2 de transforms`

> **Estado:** LISTA PARA DEV · **Fecha:** 2026-08-06 · **Confianza:** 90%

## 1. Resumen
Cuatro transforms nuevos **registrados bajo el contrato de HU-051**, sin tocar el motor:
- `shadows` (HU-053): recuperación de sombras con máscara ponderada por luminancia — levanta lo oscuro sin lavar lo claro.
- `exposure` (HU-054): corrige hacia el objetivo de brillo con protección de altas luces — la ganancia decae donde ya hay luz.
- `crop` (HU-058): recorte centrado al aspecto pedido (4:5 feed), conservador: solo recorta el eje sobrante.
- `resize` (HU-060): al nativo de plataforma con INTER_AREA (reducción de calidad fotográfica).

## 2. Fuera
- Export JPEG (HU-061) → es IO, no transform: va con la etapa (HU-064).
- Orden y valores del plan (HU-056/135) → datos del perfil; aquí solo capacidades.

## CA
- CA-1 Los 4 entran por el registro; `apply_pipeline` intacto (el test del transform falso sigue verde).
- CA-2 `shadows` sube sombras más que luces (test asimétrico); no desborda uint8.
- CA-3 `exposure` acerca el brillo medio al objetivo; una imagen ya en objetivo queda casi igual; las luces altas no se queman (test).
- CA-4 `crop` produce el aspecto exacto pedido, centrado, sin escalar; `resize` respeta dims y no deforma.
- CA-5 Params inválidos fallan al armar el plan; determinismo byte a byte; entrada intacta.
- CA-6 Cobertura ≥80% · gate-log 053/054/058/060.
