# HU-169 — Artefactos de DEV

| Artefacto | Qué es |
|---|---|
| `src/media_optimizer/core/determinism.py` | `stable_text`, `stable_order`, `stable_order_by`, `stable_unique` |
| `src/media_optimizer/core/quality_report.py` | **Arregla el defecto**: `flags` pasa de `frozenset` a tupla ordenada |
| `tests/core/test_determinism.py` | 21 tests, incluidos el arnés entre procesos y el guardián de contratos |
| `tests/core/test_quality_report.py` | Ajusta 1 aserción de igualdad |

**Lo que se esperaba encontrar no era lo que había.** "Determinismo" sugiere semillas
aleatorias, pero `testing/synthetic.py` ya usa `np.random.default_rng(seed)` —un generador
propio con semilla explícita— y **no hay aleatoriedad global en ninguna parte**. Un gestor de
semillas habría sido resolver un problema inexistente. Las dos fuentes reales se midieron:

**1. El orden de un conjunto cambia en cada ejecución del programa.** `QualityReport.flags`
era un `frozenset`, y cuatro ejecuciones con semillas de hash distintas dieron cuatro
órdenes distintos. Hoy no rompía nada porque nadie serializa los flags todavía — **HU-036 y
HU-181 iban a hacerlo**, y ahí el KPI de reproducibilidad se caía.

**2. El mismo nombre de archivo llega escrito de dos maneras.** `café.jpg` puede venir con
la `é` entera (Windows) o con la tilde suelta (macOS). Medido: `['cafz.jpg', 'café.jpg']` en
un caso y `['café.jpg', 'cafz.jpg']` en el otro. Mismos archivos, orden invertido.

**Por qué se cambió el tipo en vez de ordenar al serializar.** Ordenar en cada serializador
funciona hasta que alguien escribe uno nuevo y lo olvida; el fallo aparecería como un golden
test que falla 1 de cada N corridas con los mismos flags en otro orden — indistinguible del
ruido. Mismo criterio que en HU-168.

**Los tres guardianes se verificaron por inyección.** Restaurado el `frozenset`, fallan el
arnés entre procesos (2 tests) y el guardián de contratos, que además nombra al infractor:
`QualityReport.flags: frozenset[str]`. Ese guardián recorre todos los contratos exportados
por `core/`, así que el mismo defecto en un contrato futuro se detecta solo.

Evidencia DEV: **422 tests passed (21 nuevos) · `determinism.py` 100% · `quality_report.py` 100%**.
