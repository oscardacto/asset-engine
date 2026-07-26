# Framework Claude Code — asdd-framework

Guía de la mecánica de `.claude/` en este template. El contexto de dominio (stack,
componentes, convenciones) vive en `CLAUDE.md` — este archivo documenta solo la mecánica:
qué skills existen, cómo se activan, y qué carga Claude Code automáticamente vs. bajo
demanda.

## El ciclo

```
WorkItem  →  /new-item (DRAFT→SPEC→DEV)  →  /close-item (evidencia + cierre)  →  merge manual
```

El merge/deploy final es siempre manual — responsabilidad del equipo técnico, nunca de
Claude Code (ver "Límites de autonomía" en `CLAUDE.md`).

## Skills disponibles (`/comando` en Claude Code)

| Comando | Cuándo | Qué produce |
|---|---|---|
| `/new-item` | Arrancar o avanzar un WorkItem | `items/<ID>/{ESTADO.md, insumos/, spec/, dev/}` |
| `/close-item` | Al cerrar pruebas de desarrollo | `items/<ID>/closure/{feedback.md, entregables.md}` |

## Rules (`.claude/rules/*.md`)

Se cargan automáticamente vía el hook `rules-inject.sh` (`PreToolUse` sobre `Edit|Write`):
matchea el `file_path` contra el frontmatter `paths:` de cada rule y, si matchea, inyecta
su contenido. Ver `.claude/rules/README.md` para el formato — el directorio arranca
vacío, agrega las reglas reales de tu stack.

## Hooks (`.claude/hooks/`)

Registrados en `.claude/settings.json` bajo la clave `"hooks"` — no hay auto-discovery
por nombre de archivo.

| Script | Evento | Acción |
|---|---|---|
| `pre-edit-protection.sh` | `PreToolUse` (Edit\|Write) | Bloquea edición de archivos sensibles (`protected-patterns.json`) |
| `rules-inject.sh` | `PreToolUse` (Edit\|Write) | Inyecta `rules/*.md` según el `paths:` que matchee |
| `command-write-protection.sh` | `PreToolUse` (Bash\|PowerShell) | Bloquea comandos que escriben sobre un patrón protegido |

Ver `.claude/hooks/README.md` para semántica de exit codes y cómo agregar hooks nuevos.

## Estructura de carpetas

```
.claude/
├── README.md              ← este archivo
├── CLAUDE.md              ← contexto maestro (completar {{ASI}})
├── settings.json          ← hooks — versionado, sin secretos
├── skills/                ← /comando — ver tabla arriba
├── rules/                 ← reglas cargadas por path vía rules-inject.sh (arranca vacío)
└── hooks/                 ← pre-edit-protection, rules-inject, command-write-protection (+ .js)
```

## Referencia

Este template es la capa domain-agnostic extraída de `ClaudeCore SBS`. Los hooks se
validaron de forma aislada (payload JSON simulado por stdin) antes de incorporarse —
ver la sección "Mecanismo probado" del `README.md` raíz.
