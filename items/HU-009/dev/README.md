# HU-009 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/ingest/quarantine.py` | `QuarantineReason` (5 motivos), `QuarantinedAsset` (ruta + motivo + detalle accionable), `TriageResult` (aceptados / apartados) y `triage_media(paths)`. Detección de truncamiento por marca de cierre: JPEG `FFD9`, PNG `IEND`, WebP por el tamaño declarado en la cabecera RIFF |
| `src/media_optimizer/ingest/__init__.py` | Re-exporta los 4 nombres nuevos (13 públicos en `ingest/`) |
| `tests/ingest/test_quarantine.py` | 15 tests: el lote continúa, los 5 motivos distinguibles, truncamiento en los 3 formatos soportados, reparto disjunto y completo, determinismo, no-destructividad + capa secundaria |

**La decisión de fondo:** "cuarentena" no mueve ni copia nada. Mover tocaría el original
(prohibido por charter §6.3) y copiar duplicaría gigabytes de video sin aportar nada — así
que la cuarentena es un **registro**. Quien quiera materializarlo en disco será HU-016.

**Truncamiento sin decodificar:** cada formato soportado declara dónde termina, y eso se
comprueba leyendo solo la cola del archivo (o 12 bytes de cabecera en WebP). Captura el
caso real del archivo a medio descargar de WhatsApp por unos pocos bytes de lectura.

Mitigación de R-1 implementada: el marcador se busca **en los últimos 64 bytes**, no se
exige que sean los dos últimos exactos — algunos móviles añaden relleno tras el cierre y
exigir posición exacta habría descartado material bueno. Hay un test que lo fija.

Correcciones en DEV (batería local, antes del commit): ruff señaló dos `import` dentro de
funciones; la cobertura inicial (84%) delató la rama de WebP sin probar, lo que llevó a
unificar dos lectores de bytes en uno y añadir tests parametrizados de PNG/WebP.

Evidencia DEV (2026-07-26): **143 tests passed (15 nuevos) · cobertura `ingest/` 100%**
(172/172 stmts, gate ≥80%) · ruff check/format limpios · mypy Success (13 archivos).
