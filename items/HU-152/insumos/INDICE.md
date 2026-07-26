# Índice de insumos — HU-152

Lista los archivos entregados por el negocio/producto y su propósito.
Este directorio es **read-only mental**: no se editan los archivos originales.
Si hay correcciones, van a `closure/feedback.md`.

| Archivo | Qué es | Por qué importa |
|---------|--------|-----------------|
| hu-152-backlog.md | Extracto literal: HU del backlog + restricciones charter §6 (CPU-only, determinismo) + reglas de `python.md` + riesgo R-1 heredado de HU-151 + inventario de operaciones de visión que exige el backlog | Es el ticket: el ADR debe elegir variante de wheel (full/headless/contrib), fijar estrategia de versiones y **verificar empíricamente** los wheels CPU sobre Python 3.13.2/Windows |

Fuentes canónicas referenciadas: `docs/blueprint/backlog.md` (f10d05e) · `charter.md` §6 ·
`.claude/CLAUDE.md` · `.claude/rules/python.md` · `ADR-001` (Aceptado) ·
`items/HU-151/spec/spec_tecnica.md` §8 (R-1).
