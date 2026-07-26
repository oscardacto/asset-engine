# Rules (`.claude/rules/*.md`)

Se cargan automáticamente vía el hook `rules-inject.sh` (`PreToolUse` sobre `Edit|Write`):
matchea el `file_path` que Claude va a editar contra el frontmatter `paths:` de cada archivo
`.md` de este directorio y, si matchea, inyecta su contenido como contexto adicional de esa
llamada puntual. **No bloquea nada** — solo agrega contexto (o nada, si ninguna regla matchea).

El frontmatter `paths:` no tiene ningún mecanismo de carga nativo en Claude Code — es el
hook `rules-inject.js` el que lo hace real. Sin el hook registrado en `settings.json`, estos
archivos son metadata inerte.

## Formato de una regla

```markdown
---
description: Una línea — para qué sirve esta regla.
paths:
  - "**/*.py"
  - "**/test_*.py"
---

# Cuerpo de la regla

Todo lo que va después del frontmatter se inyecta tal cual cuando el path matchea.
```

- `paths:` acepta glob patterns (`**`, `*`) — se traducen a regex en `rules-inject.js`.
- Una regla puede matchear varios patterns; una edición puede disparar varias reglas (se
  concatenan, cada una bajo su propio encabezado `## Regla activada por path: <archivo>`).
- No hay límite de reglas ni de tamaño — pero cada regla que matchea se inyecta completa en
  cada llamada a `Edit`/`Write` sobre un path afín, así que conviene mantenerlas concisas y
  con una responsabilidad clara (una por convención de capa/lenguaje/dominio, no un catch-all).

## Sugerencia de arranque

Crea una regla por cada convención real y verificable de tu stack — no documentes aspiraciones.
Ejemplos típicos: convenciones de testing por lenguaje, estilo de commits, capas de arquitectura
que no deben mezclarse (ej. "controllers no llevan lógica de negocio"), convención de nombres de
archivos de migración. Este directorio arranca vacío a propósito — las reglas de
`ClaudeCore SBS` (`backend.md`, `frontend.md`, `database.md`, `testing.md`) son 100% específicas
del stack Java/Vue/PostgreSQL de ese proyecto y no se copian aquí.
