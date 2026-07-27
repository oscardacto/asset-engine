# Índice de insumos — HU-006

Lista los archivos entregados por el negocio/producto y su propósito.
Este directorio es **read-only mental**: no se editan los archivos originales.
Si hay correcciones, van a `closure/feedback.md`.

| Archivo | Qué es | Por qué importa |
|---------|--------|-----------------|
| hu-006-backlog.md | Extracto literal: HU del backlog + los dos usos del hash (identidad para catálogo/re-ingesta idempotente vs duplicados exactos) + el caso real de copias WhatsApp con nombres distintos + reglas de streaming y determinismo | Es el ticket: fija que el hash se lee **por bloques** (un video de 2 GB no cabe en RAM), que el agrupamiento no puede depender del orden de llegada, y que los near-duplicates perceptuales son otra HU (HU-075) |

Fuentes canónicas referenciadas: `docs/blueprint/backlog.md` (f10d05e) ·
`documento-maestro.md` §8.1 · `.claude/rules/python.md` · `.claude/CLAUDE.md` (contratos).
