# Entregables — HU-152

## PRs mergeados
| PR # | Repositorio | Rama | Descripción |
|------|-------------|------|-------------|
| [#3](https://github.com/oscardacto/asset-engine/pull/3) | oscardacto/asset-engine | `feature/HU-152-adr-opencv` → `develop` | ADR-002 stack de visión (headless) + dependencias lockeadas + test de humo. El merge ratifica el ADR |

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| `uv add opencv-python-headless>=4.10 numpy>=2.0` | Máquina de referencia | 2026-07-26 | ✅ lock actualizado (cv2 5.0.0.93, numpy 2.5.1) |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

Batería re-ejecutada sobre `develop` **después del merge** (fa1cbb0), 2026-07-26:

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 El ADR existe y decide | `docs/blueprint/adr/ADR-002-stack-vision.md` | 3 variantes comparadas, decisión única, estrategia de versiones, consecuencias | ✅ full/headless/contrib comparadas; decisión headless; floors+lock; estado ratificado | el propio archivo (b51e8ae → fa1cbb0) |
| CA-2 Dependencias lockeadas sin romper | `uv sync` en develop | termina OK, lock estable | ✅ 18 paquetes resueltos en 1 ms | log de cierre |
| CA-3 Wheels importables en 3.13.2/Win (cierra R-1 de HU-151) | `import cv2, numpy` | imprime versiones | ✅ `cv2 5.0.0 \| numpy 2.5.1` | log de cierre |
| CA-4 Build CPU-only | `test_build_de_opencv_es_cpu_only` | sin CUDA activo | ✅ passed | pytest -v |
| CA-5 Operación determinista | `test_operacion_de_vision_es_determinista` (semilla 42, GaussianBlur ×2) | arrays idénticos | ✅ passed | pytest -v |
| CA-6 Batería del esqueleto verde | pytest + ruff check/format + mypy | todo exit 0 | ✅ 3 passed · All checks passed · 49 formateados · mypy Success | log de cierre |
| CA-7 Trazabilidad | gate-log HU-152 | draft/gate_spec/dev | ✅ + qa/done de este cierre | gate-log.jsonl |

**Resultado: 7/7 criterios cumplidos · 0 fallidos · sin rework.**

## Commits relevantes
- `0d7d487` — HU-152 DRAFT+SPEC (91%, 0 bloqueantes)
- `b51e8ae` — HU-152 DEV: ADR-002 + uv add + test de humo
- `fa1cbb0` — merge PR #3 a `develop` (ratificación)
