# HU-053 (+054+058+060) — Artefactos de DEV

4 transforms registrados **sin tocar el motor** (el test del transform falso siguió verde):
`shadows` (máscara cuadrática de oscuridad: sube el interior sin lavar la ventana),
`exposure` (hacia objetivo con ganancia que decae donde ya hay luz — test de que 250 no se
quema), `crop` (centrado, solo el eje sobrante; si ya es el aspecto, ni un píxel), `resize`
(INTER_AREA). 12 tests nuevos, todos de comportamiento asimétrico o exactitud geométrica.

Evidencia: **589 tests · develop.py 100%**.
