# HU-158 — Ticket de origen (extracto literal de fuentes canónicas)

> Extracto de solo lectura. Ante discrepancia, mandan las fuentes en el repo.

## 1. La HU (backlog aprobado)

Fuente: `docs/blueprint/backlog.md`, épica E7 (commit `f10d05e`):

> | HU-158 | Contrato `QualityReport` en `core/` (métricas, flags, veredicto) | Depende de: HU-157 | P0 | S |

Dependencia satisfecha: HU-157 **DONE** (contrato `MediaAsset` en `develop`).

## 2. Qué producirán las HUs consumidoras (define la semántica de los 3 conceptos)

Fuente: `docs/blueprint/backlog.md`, E1/E2:

**Métricas** (valores numéricos por asset, el conjunto crece con E2):

> | HU-020 | Brillo medio por asset (paridad ±2% con auditoría manual del cliente 0) |
> | HU-021 | Histograma: % de píxeles en negro aplastado (umbral por perfil) |
> | HU-022 | % de altas luces quemadas |
> | HU-023 | `ADR`+impl. Métrica de nitidez (varianza de Laplaciano vs Tenengrad) |
> | HU-024 | Estimación de ruido |

**Flags** (marcas booleanas con causa, el conjunto crece con E1/E2):

> | HU-007 | Detección de compresión WhatsApp: techo 1288×952, peso, prefijo `WA` |
> | HU-008 | Flag "bajo el nativo": resolución insuficiente por formato de salida del perfil |
> | HU-034 | Detección local de rostros/placas → flag PII (no bloquea, informa) |

**Veredicto** (cerrado, 3 valores literales):

> | HU-030 | Veredicto técnico por asset: **publicable / apoyo / descartar**, con causas
> (umbrales del perfil) |

**Agregación/serialización** (consumidor directo del contrato):

> | HU-035 | `QualityReport` agregado y serializado al catálogo |

## 3. Reglas de pureza y determinismo aplicables

Fuente: `.claude/rules/python.md`:

> - `core/` y `ranking/`: funciones puras, sin IO, sin importar OpenCV/ffmpeg.
> - contratos de dominio como dataclasses (frozen cuando aplique).
> - Determinismo: semillas fijas, sin dependencia del orden del filesystem.

Fuente: `charter.md` §7 (KPI): las métricas deben reproducir la auditoría manual del
Maestro §8.2 dentro de ±2% — los valores son números comparables, no strings.

Cobertura exigida (CLAUDE.md Pre-Flight): ≥95% en dominio puro.

## 4. Alcance del ticket (los 3 conceptos, literales)

`métricas` · `flags` · `veredicto` — los umbrales que producen el veredicto son del
perfil (HU-030/133), NO de este contrato; el cálculo de cada métrica es de E2; la
asociación asset↔reporte es del catálogo (HU-012/035).
