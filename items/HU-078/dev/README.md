# HU-078 (+070+071+072+074) + HU-180/184 — Artefactos de DEV

| Artefacto | Qué es | HU |
|---|---|-----|
| `ranking/selection.py` | Dominio puro: `global_score` ponderado y normalizado (070), `cover_candidates` (071), `gallery_order` (072), `select_by_format` con elegibilidad técnica (074) | 070-074 |
| `pipeline/stages.py` (`_select`) | Etapa: analysis.json → selection.json determinista | 078 |
| `pipeline/stages.py` (`_all`) | Secuencia completa; una etapa degradada no detiene a las demás | 180/184 |
| `pipeline/reports.py` (`_selection_report`) | Portada, galería y elegibles por formato | 078 |

**La elegibilidad es técnica, no estética:** una foto que no llena el nativo de una
intención queda fuera **solo de esa intención** (flag `below_native_<intent>` de HU-008).
Test explícito: la misma foto entra en `feed` y no en `story`.

**El score normaliza por la suma de pesos** — la decisión que HU-160 dejó documentada:
ajustar un peso no obliga a recalcular los demás a mano.

**Orden narrativo:** el gancho es la mejor foto del lote; luego alterna orientación para dar
ritmo visual. La plantilla por ambientes (gancho → espacio → edificio → ubicación) necesita
el etiquetado humano (HU-032) y los ambientes del perfil (E6): entra con HU-135 sin tocar
el motor, porque `gallery_order` ya recibe el lote ya ordenado.

**`run all` reutiliza `execute_stage`**, no reimplementa nada: el orquestador es la
secuencia, y el `partial` se propaga hacia arriba (test con foto rota).

Evidencia: **607 tests · pipeline E2E validado con el lote real**.
