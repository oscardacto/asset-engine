# Índice de insumos — HU-010

Lista los archivos entregados por el negocio/producto y su propósito.
Este directorio es **read-only mental**: no se editan los archivos originales.
Si hay correcciones, van a `closure/feedback.md`.

| Archivo | Qué es | Por qué importa |
|---------|--------|-----------------|
| hu-010-backlog.md | Fila literal de la HU + lo que HU-001 dejó explícitamente pendiente + reglas del charter y `python.md` sobre entradas hostiles y resiliencia | Es el ticket. Su título describe la hipótesis original ("nombres"), que la evidencia refutó |
| evidencia-empirica.md | **Resultados ejecutados y reproducibles**: comportamiento por caso con ruta normal vs extendida (incluido el bloqueo demostrado con subproceso y timeout) + matriz de 14 operaciones × 5 casos × 2 formas de ruta sobre el stack real + limitaciones y huecos declarados | Es la base de ADR-004. Cambia la naturaleza de la HU: con ruta adaptada **no falla ninguna** de las 70 combinaciones, así que el problema nunca fueron los nombres sino la capa de acceso |

Fuentes canónicas referenciadas: `docs/blueprint/backlog.md` (f10d05e) ·
`docs/blueprint/adr/ADR-004-acceso-al-filesystem.md` · `charter.md` §6 ·
`.claude/rules/python.md` · `items/HU-001/spec` y `closure` · código de `ingest/` en `develop`.
