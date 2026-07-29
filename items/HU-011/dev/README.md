# HU-011 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/ingest/dimensions.py` | `ImageSize` (medidas + `pixels`, `longest_side`, `estimated_decoded_bytes`), `read_image_size(header, formato)` y su variante desde ruta, más los umbrales `MAX_DECODED_BYTES` (1 GiB) y `MAX_SIDE` (65.535). Parsers de cabecera para PNG (`IHDR`), JPEG (recorrido de segmentos hasta `SOF`) y WebP en sus tres variantes |
| `src/media_optimizer/ingest/quarantine.py` | Causa nueva `TOO_LARGE` + refactor de la cadena de comprobaciones (`_find_problem`, `_check_size_limits`) para que siga legible con cinco pasos |
| `tests/ingest/test_dimensions.py` | 24 tests: medidas reales en los 3 formatos, variantes VP8X/VP8/VP8L, imagen-bomba, foto de 200 MP aceptada, límite por lado, cabeceras ilegibles + capa secundaria |

**El umbral no se eligió por intuición.** El celular de referencia del cliente 0 tiene
sensor de 200 MP: una foto legítima suya son ~600 MB decodificada y **superaría el aviso
por defecto de librerías conocidas** (Pillow avisa a partir de ~89 MP). Por eso el límite
se expresa en memoria estimada (1 GiB ≈ 358 MP) y hay un test explícito que exige que una
cabecera de 200 MP se acepte.

**Verificación empírica que cambió el alcance:** al inspeccionar los bytes que produce
nuestro cv2, el WebP resultó ser **VP8L** (sin pérdida), no la variante con pérdida que
habría sido la suposición natural. Implementar solo VP8 habría fallado contra nuestros
propios fixtures. Se cubrieron las tres variantes, con cabeceras sintéticas para las dos
que cv2 no genera.

Correcciones en DEV (batería local, antes de integrar): un test mal construido (el archivo
"ilegible" resultaba rechazado antes por formato, no por dimensiones); imports
desordenados; tres números mágicos promovidos a constantes (regla propia); y **una rama
muerta eliminada** en `quarantine._is_truncated` — el `.get()` con rama `None` nunca podía
dispararse, así que pasó a acceso directo: si algún día se soporta un formato sin marca de
cierre, el `KeyError` delata el olvido en desarrollo en lugar de aceptar archivos a ciegas.

Evidencia DEV (2026-07-26): **167 tests passed (24 nuevos) · cobertura `ingest/` 100%**
(287/287 stmts, gate ≥80%) · ruff check/format limpios · mypy Success (14 archivos).
