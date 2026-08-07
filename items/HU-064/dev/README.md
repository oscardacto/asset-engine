# HU-064 (+061+065) — Artefactos de DEV

| Artefacto | Qué es | HU |
|---|---|-----|
| `pipeline/stages.py` (`_develop`) | Etapa: analizadas → reveladas en `derived/`, con historial y antes/después en `develop.json` determinista | 064 |
| export vía `cv2.imencode` + capa ADR-004 | La salida **nace sin EXIF**: sin GPS ni PII, con test que lo verifica | 061 |
| `pipeline/reports.py` (`_develop_report`) | Antes/después del lote (formato Maestro §8.4) | 065 |

- Solo se revelan publicables y de apoyo; los descartes no gastan cómputo.
- Las copias del mismo contenido se revelan **una sola vez** (identidad por hash, ADR-004).
- Nombres de salida por `safe_output_name` (HU-016): sin colisiones ni nombres hostiles.
- El plan vive como datos con `TODO(HU-135)`; **HU-056 queda abierta** hasta que el perfil
  lo declare desde archivo (E6) — el motor componible ya está (HU-051).

**Validación real (subconjunto `sala/`, 16 fotos):** oscuras de 63–75 → 113–128 de brillo,
la corrección que el revelado manual del 25-jul hacía. 2m27s por 16 fotos de celular:
lento pero funcional — el presupuesto de rendimiento es HU-063/165 y queda anotado.

Evidencia: **590 tests (11 nuevos)** · determinismo byte a byte · originales intactos.
