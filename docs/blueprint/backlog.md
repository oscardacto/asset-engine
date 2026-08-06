# Backlog — media-optimizer

**Versión 0.1 (borrador para aprobación) · 26 de julio de 2026**
Derivado del `charter.md` y de los insumos del cliente 0. Toda HU nace de aquí.

## Reglas del backlog

- Cada HU es **una línea**: la ficha completa de ingeniería (objetivo, algoritmo,
  contrato, Gherkin, plan de pruebas) se genera cuando la HU entra a SPEC vía
  `/new-item`, usando la plantilla de spec. Nada se implementa sin esa ficha aprobada
  (gate: 0 bloqueantes + ≥85% confianza).
- **Prioridad:** P0 = camino crítico al primer valor · P1 = segundo release ·
  P2 = tercero · P3 = extensión. **Estimación:** S (≤½ día) · M (1–2 días) · L (3+, candidata a partirse).
- Los IDs reservan rangos por épica; el orden de ejecución lo dan los hitos, no el ID.
- Las HUs marcadas `ADR` cierran una decisión de stack antes de que otra HU dependa de ella.

## Hitos (releases incrementales)

| Hito | Entrega | Épicas involucradas | Valor para el cliente 0 |
|------|---------|---------------------|--------------------------|
| **M1 — Auditoría reproducible** | `ingest` + `analyze` + reporte | E7, E1, E2, E6 (parcial) | Reproduce la auditoría manual del Maestro §8.2 con un comando |
| **M2 — Revelado determinista** | `develop` por lotes | E3, E6 | Reemplaza el revelado manual del 25-jul, con golden tests |
| **M3 — Selección y galería** | `rank` / `select` | E4 | Portada, orden narrativo y cobertura de ambientes |
| **M4 — Reels** | `reel` | E5, E8 | Verticales 9:16 desde clips crudos |

---

## E7 · Plataforma (HU-150–169) — el esqueleto va primero

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-150 | Esqueleto del repo: `pyproject.toml`, layout `src/`, ruff+mypy+pytest configurados con los límites de `.claude/rules/python.md` | — | P0 | M |
| HU-151 | `ADR` Gestor de entorno y dependencias (venv+pip vs uv) | — | P0 | S |
| HU-152 | `ADR` OpenCV+NumPy como base de visión (versiones, wheels CPU) | HU-150 | P0 | S |
| HU-153 | `ADR` Catálogo local: manifiestos JSON vs SQLite | HU-150 | P0 | S |
| HU-154 | `ADR` Stack de video: ffmpeg + PySceneDetect (y PyAV sí/no). **Obligatorio: validar la cadena contra la matriz de compatibilidad de rutas de ADR-004 antes de adoptarla** | HU-150 | P2 | S |
| HU-155 | Configuración externalizada: carga, validación y defaults (`config/`) | HU-150 | P0 | M |
| HU-156 | Logging estructurado base (JSON lines, niveles, cero `print`) | HU-150 | P0 | S |
| HU-157 | Contrato `MediaAsset` en `core/` (foto/video, dimensiones, hash, origen) | HU-150 | P0 | M |
| HU-158 | Contrato `QualityReport` en `core/` (métricas, flags, veredicto) | HU-157 | P0 | S |
| HU-159 | Contrato `Transform` + historial de transformaciones aplicadas | HU-157 | P0 | S |
| HU-160 | Contrato `BusinessProfile` en `core/` (solo estructura; datos en E6) | HU-150 | P0 | S |
| HU-161 | Jerarquía de excepciones del dominio (corrupto ≠ inválido ≠ bug) | HU-150 | P0 | S |
| HU-162 | CLI base con argparse (ADR-005): entrypoint, `--version`, contexto global, codigos de salida y traduccion de errores | HU-150 | P0 | S |
| HU-163 | Gates de calidad locales: pre-commit con ruff+mypy+pytest dirigido | HU-150 | P0 | S |
| HU-164 | Framework de golden tests (comparación de imágenes con tolerancia + hash) | HU-150 | P0 | M |
| HU-165 | Framework de benchmarks con presupuestos por etapa (`benchmarks/`) | HU-150 | P1 | M |
| HU-166 | Generador de fixtures sintéticos de imagen (exposiciones, orientaciones, corruptos) | HU-150 | P0 | M |
| HU-167 | Generador de fixtures sintéticos de video (clips cortos, escenas, corruptos) | HU-154 | P2 | M |
| HU-168 | Contrato `StageReport`: tiempo, memoria pico, transformaciones, scores por etapa | HU-150 | P0 | S |
| HU-169 | Utilidades de determinismo: semillas fijas, orden estable, test de reproducibilidad E2E | HU-150 | P0 | S |
| HU-170 | Histórico de auditoría de lotes: herramienta versionada que acumula por lote totales, duplicados, formatos, EXIF, resoluciones y causas de cuarentena, para medir si el pipeline mejora entre lotes | HU-017 | P1 | M |

## E1 · Ingesta y catálogo (HU-001–019)

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-001 | Escaneo de carpeta de entrada con orden determinista e independiente del filesystem | HU-157 | P0 | S |
| HU-002 | Validación de formatos de imagen soportados (magic bytes, no extensión) | HU-001 | P0 | S |
| HU-003 | Validación de formatos de video soportados (codecs esperados) | HU-001, HU-154 | P2 | S |
| HU-004 | Lectura segura de EXIF: malformado o ausente degrada el asset, no tumba el lote | HU-002 | P0 | M |
| HU-005 | Detección de orientación V/H (dimensiones + EXIF Orientation) | HU-004 | P0 | S |
| HU-006 | Hash de contenido y detección de duplicados exactos | HU-001 | P0 | S |
| HU-007 | Detección de compresión WhatsApp: techo 1288×952, peso, prefijo `WA` (KPI: 43/43 del cliente 0, 0 FP en serie 4-abr) | HU-002 | P0 | M |
| HU-008 | Flag "bajo el nativo": resolución insuficiente por formato de salida del perfil (1080/1350/1920) | HU-007, HU-160 | P0 | S |
| HU-009 | Archivos corruptos o truncados: cuarentena con causa, pipeline sigue | HU-002, HU-161 | P0 | M |
| HU-010 | Capa de acceso al filesystem: rutas que hoy detienen el pipeline (ADR-004) | HU-001 | P0 | M |
| HU-011 | Límites de memoria y dimensiones: rechazo de imágenes-bomba antes de decodificar | HU-002 | P0 | M |
| HU-012 | Persistencia del catálogo (según ADR HU-153) con escritura atómica | HU-153, HU-157 | P0 | M |
| HU-013 | Re-ingesta idempotente: mismo input no duplica ni reprocesa | HU-012 | P0 | M |
| HU-014 | Metadatos de video: duración, fps, resolución, codec, bitrate | HU-003 | P2 | S |
| HU-015 | Agrupación por sesión de captura (fecha/hora EXIF → series tipo "4 de abril") | HU-004 | P1 | M |
| HU-016 | Directorio de trabajo no destructivo: layout de salidas + verificación de que el origen queda intacto + **saneamiento de nombres al escribir, vía la capa de ADR-004** | HU-012, HU-010 | P0 | S |
| HU-017 | CLI `ingest`: carpeta → catálogo + resumen en consola | HU-162, HU-012 | P0 | S |
| HU-018 | Reporte de inventario del lote (tabla por asset: dims, orientación, flags — formato Maestro §8.2) | HU-017 | P0 | S |
| HU-019 | Sidecar de etiquetas manuales (ambiente, descarte, notas) que sobrevive re-ingestas | HU-013 | P1 | M |

## E2 · Análisis de calidad — foto (HU-020–049)

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-020 | Brillo medio por asset (paridad ±2% con auditoría manual del cliente 0) | HU-158, HU-166 | P0 | S |
| HU-021 | Histograma: % de píxeles en negro aplastado (umbral por perfil) | HU-020 | P0 | S |
| HU-022 | % de altas luces quemadas | HU-020 | P0 | S |
| HU-023 | `ADR`+impl. Métrica de nitidez (varianza de Laplaciano vs Tenengrad) | HU-158 | P0 | M |
| HU-024 | Estimación de ruido | HU-023 | P1 | M |
| HU-025 | Detección de desenfoque de movimiento (vs desenfoque óptico) | HU-023 | P1 | M |
| HU-026 | Estimación de temperatura de color / dominante | HU-020 | P1 | M |
| HU-027 | Contraste global y por zonas (¿la ventana quema al interior?) | HU-021 | P1 | M |
| HU-028 | Detección de verticales inclinadas (líneas de arquitectura, ángulo de corrección) | HU-023 | P1 | L |
| HU-029 | Score de exposición compuesto (fórmula = datos del perfil) | HU-020–022, HU-160 | P0 | S |
| HU-030 | Veredicto técnico por asset: publicable / apoyo / descartar, con causas (umbrales del perfil) | HU-029 | P0 | S |
| HU-031 | `ADR` Estrategia de detección de ambientes sin nube ni entrenamiento (heurística vs modelo local pre-entrenado) | HU-030 | P1 | M |
| HU-032 | Etiquetado asistido de ambientes vía CLI (propone, humano confirma → sidecar HU-019) | HU-031, HU-019 | P1 | M |
| HU-033 | Cobertura de ambientes del lote vs esperados por el perfil (qué falta grabar) | HU-032, HU-160 | P1 | S |
| HU-034 | Detección local de rostros/placas → flag PII (no bloquea, informa) | HU-031 | P2 | M |
| HU-035 | `QualityReport` agregado y serializado al catálogo | HU-030 | P0 | S |
| HU-036 | Reporte comparativo del lote: tablas ordenadas por score, estrellas y descartes | HU-035 | P0 | S |
| HU-037 | CLI `analyze`: catálogo → reportes + flags | HU-017, HU-035 | P0 | S |
| HU-038 | Golden test integral de análisis sobre fixtures sintéticos + validación manual vs Maestro §8.2 | HU-037, HU-164 | P0 | M |

## E3 · Revelado (HU-050–069)

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-050 | Corrección de perspectiva/verticales (a partir del ángulo de HU-028) | HU-028, HU-159 | P1 | L |
| HU-051 | CLAHE parametrizado por perfil (clip limit, tiles) | HU-159 | P1 | M |
| HU-052 | White balance con calidez solo en luces (referencia: revelado 25-jul) | HU-026, HU-159 | P1 | M |
| HU-053 | Recuperación de sombras con máscara ponderada por luminancia | HU-021, HU-159 | P1 | L |
| HU-054 | Exposición hacia objetivo con protección de altas luces | HU-053 | P1 | M |
| HU-055 | Control de saturación con tope del perfil (cliente 0: ≤6%) | HU-052 | P1 | S |
| HU-056 | Pipeline de revelado componible: orden y parámetros de transforms declarados en el perfil | HU-051–055 | P1 | M |
| HU-057 | Historial de transformaciones por asset (sidecar auditable) | HU-056 | P1 | S |
| HU-058 | Crop 4:5 para feed con encuadre conservador (recorte lateral mínimo) | HU-056 | P1 | M |
| HU-059 | Salida 9:16 para stories desde verticales (crop o extensión según perfil) | HU-056 | P2 | M |
| HU-060 | Redimensionado al nativo de plataforma con resampling de calidad | HU-058 | P1 | S |
| HU-061 | Export JPEG: calidad configurable, metadatos limpios (sin GPS/PII) | HU-060 | P1 | S |
| HU-062 | Golden tests del revelado calibrados contra el antes/después del 25-jul | HU-056, HU-164 | P1 | M |
| HU-063 | Presupuesto de rendimiento por foto (benchmark, CPU de referencia) | HU-062, HU-165 | P1 | S |
| HU-064 | CLI `develop`: lote → directorio de trabajo con revelados | HU-056, HU-037 | P1 | S |
| HU-065 | Reporte antes/después del lote (brillo medio, % negro — formato Maestro §8.4) | HU-064 | P1 | S |

## E4 · Ranking y selección (HU-070–099)

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-070 | Score global por asset: combinación ponderada según pesos del perfil | HU-035, HU-160 | P1 | M |
| HU-071 | Candidatas a portada: top-N con criterios de portada del perfil (luminosa, amplia, nativa) | HU-070 | P1 | M |
| HU-072 | Orden narrativo de galería según plantilla del perfil (gancho → espacio → edificio → ubicación) | HU-070, HU-033 | P1 | L |
| HU-073 | Cobertura de ambientes en la selección: penalizar huecos y redundancia | HU-072 | P1 | M |
| HU-074 | Selección por formato de salida: portada / feed 4:5 / story 9:16, con elegibilidad técnica | HU-070, HU-008 | P1 | M |
| HU-075 | Detección de near-duplicates para diversidad de la selección | HU-006, HU-070 | P1 | M |
| HU-076 | Ranking explicable: por qué cada asset quedó dentro/fuera (trazas legibles) | HU-070 | P1 | S |
| HU-077 | Matching de assets contra un plan de piezas (calendario del perfil: qué pieza queda bloqueada por falta de material) | HU-074 | P2 | M |
| HU-078 | CLI `select`: catálogo analizado → selección + galería ordenada | HU-072, HU-064 | P1 | S |
| HU-079 | Golden test de ranking: determinista ante mismo catálogo y perfil | HU-078, HU-164 | P1 | S |

## E5 · Video y reels (HU-100–129)

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-100 | Ingesta de clips: validación, metadatos, streaming (nunca el video completo a RAM) | HU-014 | P2 | M |
| HU-101 | Detección de escenas (PySceneDetect, umbrales por perfil) | HU-100, HU-154 | P2 | M |
| HU-102 | Score técnico por escena: nitidez, exposición, estabilidad (muestreo de frames) | HU-101, HU-029 | P2 | L |
| HU-103 | Descarte de escenas malas con causas | HU-102 | P2 | S |
| HU-104 | Crop 9:16 de material horizontal (encuadre centrado configurable) | HU-101 | P2 | M |
| HU-105 | Secuenciado narrativo según plantilla del perfil (ej. guion R1: umbral → sala → balcón → cocina → baño → cierre) | HU-103, HU-135 | P2 | L |
| HU-106 | Recorte de clips a duración objetivo por segmento de la plantilla | HU-105 | P2 | M |
| HU-107 | Ensamblado del reel con ffmpeg: concatenación + transiciones simples | HU-106 | P2 | M |
| HU-108 | Normalización de color/exposición entre clips del mismo reel | HU-107, HU-052 | P3 | L |
| HU-109 | Export 1080×1920: codec, bitrate y perfil de color por plataforma | HU-107 | P2 | S |
| HU-110 | CLI `reel`: clips → reel 9:16 + reporte de escenas usadas/descartadas | HU-109 | P2 | S |
| HU-111 | Golden test de reel determinista (mismos clips + perfil ⇒ mismo output) | HU-110, HU-164 | P2 | M |
| HU-112 | Presupuesto de rendimiento por minuto de material crudo | HU-110, HU-165 | P2 | S |

## E6 · Perfiles de negocio (HU-130–149)

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-130 | Esquema del perfil: estructura, tipos y validación (carga falla rápido y claro) | HU-160 | P0 | M |
| HU-131 | Carga con defaults del sistema + overrides del perfil | HU-130 | P0 | S |
| HU-132 | Perfil `hospedaje` v1 con datos del cliente 0: ambientes esperados, estética (sat ≤6%, sin HDR), formatos (4:5, 9:16, nunca 1:1) | HU-130 | P0 | M |
| HU-133 | Umbrales técnicos por perfil: descarte, flags, objetivos de exposición | HU-132 | P0 | S |
| HU-134 | Pesos del score por perfil (portada vs feed vs story) | HU-132 | P1 | S |
| HU-135 | Plantillas narrativas como datos: orden de galería y guiones de reel | HU-132 | P1 | M |
| HU-136 | Perfil hostil o incompleto: mensajes de error accionables, nunca stacktrace | HU-130 | P0 | S |
| HU-137 | Guía + perfil de ejemplo para una vertical nueva (validar generalización) | HU-132 | P3 | S |

## E8 · Pipeline y reportes (HU-180–199)

| ID | HU | Depende de | Prio | Est |
|----|----|-----------|------|-----|
| HU-180 | Orquestador de etapas: un asset que falla degrada, el lote continúa; resumen de fallos | HU-161, HU-168 | P0 | M |
| HU-181 | Reporte consolidado del run en Markdown (inventario + análisis + selección) | HU-036, HU-076 | P1 | M |
| HU-182 | Reanudación idempotente: re-ejecutar un run no repite trabajo hecho | HU-013, HU-180 | P1 | M |
| HU-183 | Métricas de run en JSONL (tiempos, memoria, conteos) para auditoría histórica | HU-168 | P1 | S |
| HU-184 | CLI `run`: pipeline completo ingest→analyze→develop→select con un comando | HU-180, HU-078 | P1 | S |
| HU-185 | Smoke test E2E con dataset sintético en CI local (< 60 s) | HU-184, HU-166 | P1 | M |

---

**Total: 111 HUs** · P0: 43 (hito M1) · P1: 41 (M2–M3) · P2: 22 (M4) · P3: 5.

## Orden de arranque propuesto (primeras 10)

`HU-151` → `HU-150` → `HU-152` → `HU-157` → `HU-158` → `HU-161` → `HU-166` →
`HU-001` → `HU-002` → `HU-020` — con eso hay un `analyze` embrionario que ya
calcula brillo sobre fixtures y se puede validar contra la primera fila del Maestro §8.2.
