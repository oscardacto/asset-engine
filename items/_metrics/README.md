# items/_metrics — métricas estructuradas del proceso ASDD

Cierra un riesgo aceptado del template original: "pasó el gate" era una frase en un
`.md`, sin registro consultable. Aquí el gate y el cierre dejan **datos**: con ~20 HUs
acumuladas se puede responder si la confianza declarada (85% vs 95%) predice bugs reales
en QA, cuánto tarda DRAFT→DEV, y qué categorías de bloqueantes se repiten.

## `gate-log.jsonl`

**Append-only** — una línea JSON por evento, nunca se reescribe ni se edita una línea
existente. Lo escriben los skills `/new-item` y `/close-item`.

| evento | quién | campos adicionales a `item`, `evento`, `fecha` |
|--------|-------|-----------------------------------------------|
| `draft` | /new-item | — |
| `gate_spec` | /new-item | `intento`, `confianza` (0-100), `bloqueantes`, `importantes`, `informativas`, `resultado` (`LISTA_PARA_DEV` \| `REQUIERE_REFINAMIENTO` \| `NO_VIABLE`) |
| `dev` | /new-item | — |
| `qa` | /close-item | `criterios_total`, `criterios_fallidos`, `rework` (bool), `notas` |
| `done` | /close-item | — |

Reglas: `fecha` en `YYYY-MM-DD`; `item` = ID exacto de la carpeta en `items/`;
`gate_spec` se registra en **cada** evaluación (los intentos fallidos son el dato más
valioso, no se borran).

## Consultas de ejemplo (PowerShell)

```powershell
$ev = Get-Content items/_metrics/gate-log.jsonl | ForEach-Object { $_ | ConvertFrom-Json }

# ¿La confianza declarada predice el resultado de QA?
$gates = $ev | Where-Object { $_.evento -eq 'gate_spec' -and $_.resultado -eq 'LISTA_PARA_DEV' }
foreach ($g in $gates) {
  $q = $ev | Where-Object { $_.evento -eq 'qa' -and $_.item -eq $g.item }
  [pscustomobject]@{ item=$g.item; confianza=$g.confianza; rework=$q.rework; fallidos=$q.criterios_fallidos }
}

# Tiempo DRAFT→DEV por HU (días)
$ev | Group-Object item | ForEach-Object {
  $d = $_.Group | Where-Object evento -eq 'draft'; $v = $_.Group | Where-Object evento -eq 'dev'
  if ($d -and $v) { [pscustomobject]@{ item=$_.Name; dias=([datetime]$v.fecha - [datetime]$d.fecha).Days } }
}

# ¿Cuántos intentos de gate necesita una HU en promedio?
$ev | Where-Object evento -eq 'gate_spec' | Group-Object item |
  Measure-Object -Property Count -Average
```

Cuando haya suficientes datos (~20 HUs), un tablero vivo es candidato a HU propia de
`E7-plataforma` — no antes (sería ceremonia sin datos que mirar).
