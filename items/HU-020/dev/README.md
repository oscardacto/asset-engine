# HU-020 (+021+022) — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/vision/exposure.py` | `decode_image`, `luminance`, `mean_brightness`, `crushed_shadows_ratio`, `blown_highlights_ratio` |
| `tests/vision/test_exposure.py` | 30 tests sobre imágenes de valores conocidos |

**La decisión que protege el KPI:** el brillo es **luminancia perceptual** (Rec. 601), no
promedio de canales. La auditoría del cliente se hizo a ojo, y el ojo pesa el verde ~5×
más que el azul. Hay test con colores puros que fija los tres coeficientes y el orden BGR
de OpenCV: si alguien los invirtiera, rojo y azul intercambiarían valores y el test cae.

**`decode_image` nunca le da la ruta a OpenCV**: lee los bytes por la capa de ADR-004 y
decodifica en memoria. Probado en ruta >260 caracteres, donde `cv2.imread` muere.

**Umbrales como parámetros**, jamás constantes: qué es "negro" o "quemado" es criterio del
perfil (HU-133).

**Validación con medios reales:** las fotos editadas del anuncio dan brillo 126–144 con
<1–8% de negro; las crudas del celular, brillo 65–97 con hasta 24% de negro — el mismo
patrón que la auditoría manual del Maestro §8.2 registró.

**Dos defectos de test corregidos durante DEV** (no de producción): la frontera exacta del
umbral no existe en float sobre BGR (se prueba en grises, donde sí es exacta), y sembrar en
ruta larga exige el prefijo extendido.

Evidencia DEV: **521 tests (30 nuevos) · `exposure.py` 100%** · ruff y mypy limpios.
