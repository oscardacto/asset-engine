# Entregables — HU-157

## PRs mergeados
| PR # | Repositorio | Rama | Descripción |
|------|-------------|------|-------------|
| [#4](https://github.com/oscardacto/asset-engine/pull/4) | oscardacto/asset-engine | `feature/HU-157-media-asset` → `develop` | Contrato `MediaAsset` en `core/` + 17 tests. El merge ratifica A-1 (naming inglés + docs español) |

## Migraciones/scripts ejecutados
| Script | Ambiente | Fecha ejecución | Estado |
|--------|----------|-----------------|--------|
| N/A — dominio puro, sin instalaciones ni migraciones | — | — | — |

## Evidencia de pruebas (contra criterios de aceptación de la spec §11)

Batería ejecutada sobre `develop` post-merge (49f9491) y re-verificada tras la limpieza
de docstrings (c4c52cb), 2026-07-26:

| CA | Input probado | Resultado esperado | Resultado real | Evidencia |
|----|---------------|---------------------|-----------------|-----------|
| CA-1 Construcción foto/video | `TestCA1Construccion` (2 tests) | expone los 4 conceptos del ticket | ✅ passed | pytest |
| CA-2 Inmutabilidad | `TestCA2Inmutabilidad` — asignar `width` | `FrozenInstanceError` | ✅ passed | pytest |
| CA-3 Invariantes fail-fast | `TestCA3InvariantesFailFast` — width=0, height=-1, hash="" | `ValueError` nombrando campo y valor | ✅ passed (3 tests, `match` sobre el mensaje) | pytest |
| CA-4 Orientación | `TestCA4Orientacion` — 1080×1920 / 1920×1080 / 1000×1000 | V / H / SQUARE | ✅ passed (parametrizado) | pytest |
| CA-5 Igualdad por valor | `TestCA5IgualdadPorValor` | iguales ⇔ mismos campos | ✅ passed (2 tests) | pytest |
| CA-6 Pureza + tipado | Inspección de imports + `mypy src/` estricto | solo stdlib; exit 0 | ✅ `dataclasses`/`enum`/`pathlib` únicamente · mypy Success (3 archivos) | código + log |
| CA-7 Cobertura dominio puro | `pytest --cov=media_optimizer.core` | ≥ 95% | ✅ **100%** (36/36 stmts) | log de cobertura |
| CA-8 Batería completa | pytest · ruff check/format · mypy | todo exit 0 | ✅ 17 passed · limpio · Success | log de cierre |
| CA-9 Trazabilidad | gate-log HU-157 | draft/gate_spec/dev | ✅ + qa/done de este cierre | gate-log.jsonl |

**Resultado: 9/9 criterios cumplidos · 0 fallidos · sin rework.**
Capa secundaria (etiquetada): 3 boundary tests adicionales (1×1, hash de espacios, StrEnum serializa plano).

## Commits relevantes
- `b6cf138` — HU-157 DRAFT+SPEC (92%, 0 bloqueantes)
- `ec28053` — HU-157 DEV: contrato + tests
- `49f9491` — merge PR #4 a `develop`
- `c4c52cb` — post-merge: docstrings a la nueva convención (feedback del equipo, ver feedback.md)
