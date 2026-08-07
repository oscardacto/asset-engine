# HU-007 (+008) — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/ingest/degradation.py` | `whatsapp_compression` + `below_native` + umbral calibrado exportado |
| `tests/ingest/test_degradation.py` | 19 tests con los números del lote real |

**La señal del enunciado se midió y quedó obsoleta.** El techo 1288×952 habría dado 16/16
falsos negativos: las fotos WA reales miden 4080×3060 (WhatsApp reenvía en HD). La regla
calibrada: **nombre WA** (suficiente) **o EXIF ausente ∧ <0.15 bytes/píxel**. El margen es
ancho y medido: WA máx 0.114; lo más comprimido no-WA sin EXIF, 0.234.

**KPI validado sobre el lote real completo: 16/16 detectadas · 0 falsos positivos en 86.**
La serie de 43 se re-valida cuando llegue (insumo pendiente ya registrado).

**`below_native` reutiliza `OutputFormat` de HU-160** y admite la foto girada: una vertical
de 3060×4080 sí alcanza para un formato horizontal, porque el recorte puede rotar el
encuadre.

Evidencia DEV: **540 tests (19 nuevos) · `degradation.py` 100%** · ruff y mypy limpios.
