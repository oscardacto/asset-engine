# Índice de insumos — HU-012

Lista los archivos entregados por el negocio/producto y su propósito.
Este directorio es **read-only mental**: no se editan los archivos originales.
Si hay correcciones, van a `closure/feedback.md`.

| Archivo | Qué es | Por qué importa |
|---------|--------|-----------------|
| hu-012-backlog.md | Extracto literal: HU del backlog + los 7 consumidores que dictan los campos (HU-013 idempotencia, HU-018 dims/flags, HU-035 reportes de calidad, HU-019 etiquetas manuales…) + la decisión ya tomada en ADR-003 (JSON ordenado, escritura atómica obligatoria) + contratos del dominio disponibles | Es el ticket: el formato **ya está decidido**, así que lo que esta HU resuelve es el **esquema** (qué campos y cómo evolucionan sin romper lo anterior) y la **escritura que no puede corromper** el catálogo |

Fuentes canónicas referenciadas: `docs/blueprint/backlog.md` (f10d05e) ·
`docs/blueprint/adr/ADR-003-catalogo-local.md` (Aceptado) · `charter.md` §6 ·
`.claude/rules/python.md` · código en `develop` (`f13f6eb`).
